from django.utils.translation import gettext_lazy as _, gettext
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework import status
from easysnmp import EasySNMPTimeoutError
from django_filters.rest_framework import DjangoFilterBackend

from devices.base_intr import DeviceImplementationError
from djing2.lib import ProcessLocked
from djing2.viewsets import DjingModelViewSet, DjingListAPIView
from devices.models import Device, Port
from devices import serializers as dev_serializers
from devices.tasks import onu_register
from groupapp.models import Group


def catch_dev_manager_err(fn):
    def wrapper(self, request, pk=None):
        try:
            return fn(self, request, pk)
        except DeviceImplementationError as err:
            return Response({'Error': {
                'text': '%s' % err
            }}, status=status.HTTP_501_NOT_IMPLEMENTED)
        except EasySNMPTimeoutError as err:
            return Response({'Error': {
                'text': err
            }}, status=status.HTTP_408_REQUEST_TIMEOUT)

    # Hack for decorator @action
    wrapper.__name__ = fn.__name__
    return wrapper


class DeviceModelViewSet(DjingModelViewSet):
    queryset = Device.objects.all()
    serializer_class = dev_serializers.DeviceModelSerializer
    filterset_fields = ('group', 'dev_type', 'status', 'is_noticeable')
    filter_backends = (SearchFilter, DjangoFilterBackend)
    search_fields = ('comment', 'ip_address', 'mac_addr')

    def destroy(self, *args, **kwargs):
        r = super().destroy(*args, **kwargs)
        onu_register.delay(
            tuple(dev.pk for dev in Device.objects.exclude(group=None).only('pk').iterator())
        )
        return r

    def create(self, *args, **kwargs):
        r = super().create(*args, **kwargs)
        onu_register.delay(
            tuple(dev.pk for dev in Device.objects.exclude(group=None).only('pk').iterator())
        )
        return r

    @action(detail=True)
    def scan_units_unregistered(self, request, pk=None):
        device = self.get_object()
        manager = device.get_manager_object()
        if hasattr(manager, 'get_fibers'):
            unregistered = map(
                lambda fiber: filter(
                    lambda onu: onu is not None, manager.get_units_unregistered(
                        int(fiber.get('fb_id'))
                    )
                ), manager.get_fibers()
            )
            print(unregistered, list(unregistered))
            return Response(unregistered)
        return Response({'Error': {
            'text': 'Manager has not get_fibers attribute'
        }})

    @action(detail=True)
    @catch_dev_manager_err
    def scan_ports(self, request, pk=None):
        device = self.get_object()
        manager = device.get_manager_object()
        ports = tuple(manager.get_ports())
        if ports is not None and len(ports) > 0 and isinstance(
            ports[0],
            Exception
        ):
            return Response({'Error': {
                'text': '%s' % ports[1]
            }})
        return Response(p.to_dict() for p in ports)

    @action(detail=True)
    @catch_dev_manager_err
    def scan_details(self, request, pk=None):
        device = self.get_object()
        manager = device.get_manager_object()
        data = manager.get_details()
        return Response(data)

    @action(detail=True)
    @catch_dev_manager_err
    def scan_fibers(self, request, pk=None):
        device = self.get_object()
        manager = device.get_manager_object()
        if hasattr(manager, 'get_fibers'):
            fb = manager.get_fibers()
            return Response(fb)
        else:
            return Response({'Error': {
                'text': 'Manager has not get_fibers attribute'
            }})

    @action(detail=True, methods=['put'])
    @catch_dev_manager_err
    def send_reboot(self, request, pk=None):
        device = self.get_object()
        manager = device.get_manager_object()
        manager.reboot(save_before_reboot=False)
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    @catch_dev_manager_err
    def toggle_port(self, request, pk=None):
        device = self.get_object()
        manager = device.get_manager_object()
        port_id = request.query_params.get('port_id')
        port_state = request.query_params.get('state')
        if not port_id or not port_id.isdigit():
            return Response(_('Parameter port_id is bad'), status=status.HTTP_400_BAD_REQUEST)
        ports = tuple(manager.get_ports())
        port_id = int(port_id)
        if port_state == 'up':
            ports[port_id - 1].enable()
        elif port_state == 'down':
            ports[port_id - 1].disable()
        else:
            return Response(_('Parameter port_state is bad'), status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    @catch_dev_manager_err
    def fix_onu(self, request, pk=None):
        onu = self.get_object()
        parent = onu.parent_dev
        if parent is not None:
            manager = onu.get_manager_object()
            mac = onu.mac_addr
            ports = manager.get_list_keyval('.1.3.6.1.4.1.3320.101.10.1.1.3')
            text = _('Device with mac address %(mac)s does not exist') % mac
            http_status = status.HTTP_404_NOT_FOUND
            for srcmac, snmpnum in ports:
                # convert bytes mac address to str presentation mac address
                real_mac = ':'.join('%x' % ord(i) for i in srcmac)
                if mac == real_mac:
                    onu.snmp_extra = str(snmpnum)
                    onu.save(update_fields=('snmp_extra',))
                    text = _('Fixed')
                    http_status = status.HTTP_200_OK
        else:
            text = _('Parent device not found')
            http_status = status.HTTP_404_NOT_FOUND
        return Response(text, http_status)

    @action(detail=True, methods=['get'])
    @catch_dev_manager_err
    def register_device(self, request, pk=None):
        from devices import expect_scripts
        device = self.get_object()
        http_status = status.HTTP_200_OK
        try:
            device.register_device()
        except expect_scripts.OnuZteRegisterError:
            text = gettext('Unregistered onu not found')
        except expect_scripts.ZteOltLoginFailed:
            text = gettext('Wrong login or password for telnet access')
        except (
                ConnectionRefusedError, expect_scripts.ZteOltConsoleError,
                expect_scripts.ExpectValidationError, expect_scripts.ZTEFiberIsFull
        ) as e:
            text = e
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE
        except ProcessLocked:
            text = gettext('Process locked by another process')
        else:
            text = gettext('ok')
        return Response(text, status=http_status)


class DeviceWithoutGroupListAPIView(DjingListAPIView):
    queryset = Device.objects.filter(group=None)
    serializer_class = dev_serializers.DeviceWithoutGroupModelSerializer


class PortModelViewSet(DjingModelViewSet):
    queryset = Port.objects.all()
    serializer_class = dev_serializers.PortModelSerializer


class DeviceGroupsList(DjingListAPIView):
    serializer_class = dev_serializers.DeviceGroupsModelSerializer

    def get_queryset(self):
        groups = get_objects_for_user(
            self.request.user,
            'groupapp.view_group', klass=Group,
            accept_global_perms=False
        )
        return groups
