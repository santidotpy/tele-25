from mininet.net import Mininet
from mininet.node import Controller, Node, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import argparse

def myNetwork(sucursales):
    switches_wan = []
    switches_lan = []
    routers = []
    hosts = []

    net = Mininet(topo=None,
                  build=False,
                  ipBase='10.0.0.0/8')

    info('*** Adding controller (none used)\n')

    info('*** Add switches\n')
    for i in range(sucursales):
        switches_lan.append(net.addSwitch(f's{i+1}_lan', cls=OVSKernelSwitch, failMode='standalone'))
        switches_wan.append(net.addSwitch(f's{i+1}_wan', cls=OVSKernelSwitch, failMode='standalone'))

    info('*** Add central router\n')
    r_central = net.addHost('r_central', cls=Node, ip='')
    r_central.cmd('sysctl -w net.ipv4.ip_forward=1')

    info('*** Add branch routers\n')
    for i in range(sucursales):
        router = net.addHost(f'r{i+1}', cls=Node, ip='')
        router.cmd('sysctl -w net.ipv4.ip_forward=1')
        routers.append(router)

    info('*** Add hosts\n')
    for i in range(sucursales):
        ip = f'10.0.{i}.254/24'
        hosts.append(net.addHost(f'h{i+1}', ip=ip, defaultRoute=None))

    info('*** Add links\n')
    for i in range(sucursales):
        # WAN IPs
        ip_r_central = f'192.168.100.{6 + 8 * i}/29'
        ip_r_branch_wan = f'192.168.100.{1 + 8 * i}/29'
        # LAN IPs
        ip_r_branch_lan = f'10.0.{i}.1/24'
        ip_host = f'10.0.{i}.254/24'

        # Links
        net.addLink(r_central, switches_wan[i], params1={'ip': ip_r_central})
        net.addLink(routers[i], switches_wan[i], params1={'ip': ip_r_branch_wan})

        net.addLink(routers[i], switches_lan[i], params1={'ip': ip_r_branch_lan})
        net.addLink(hosts[i], switches_lan[i], params1={'ip': ip_host})

    info('*** Building network\n')
    net.build()

    info('*** Starting switches\n')
    for sw in switches_wan + switches_lan:
        sw.start([])

    info('*** Configuring routes\n')
    for i in range(sucursales):
        # Router Central: ruta hacia cada LAN
        net['r_central'].cmd(f"ip route add 10.0.{i}.0/24 via 192.168.100.{1 + 8 * i}")
        # Routers de sucursales: default vía r_central
        routers[i].cmd(f"ip route add default via 192.168.100.{6 + 8 * i}")
        # Hosts: default vía router LAN
        hosts[i].cmd(f"ip route add default via 10.0.{i}.1")

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    parser = argparse.ArgumentParser()
    parser.add_argument("sucursales", help="Cantidad de sucursales a crear", type=int)
    args = parser.parse_args()
    myNetwork(args.sucursales)