#!/bin/sh
uci set diffserv.@general[0].enabled=0
uci set diffserv.@general[0].low_latency=1
uci set diffserv.@general[0].diversity_rates=1
uci set network.mesh_dev.num_bcasts_own=1
uci set network.mesh_dev.num_bcasts_other=0
uci set network.bat0.orig_interval=5000
uci set simpleconfig.@commonholders[0].aggr_tpc=0
uci set simpleconfig.@commonholders[0].tpc=0
uci set simpleconfig.@commonholders[0].distance=10
uci set simpleconfig.@commonholders[0].low_latency=1
uci set simpleconfig.@commonholders[0].nodes_in_network=11_to_100
uci set simpleconfig.@commonholders[0].ogm_interval_in_ms=5000
uci set simpleconfig.@general[0].aggr_tpc=0
uci set simpleconfig.@general[0].tpc=0
uci set simpleconfig.@general[0].distance=10
uci set simpleconfig.@general[0].low_latency=1
uci set simpleconfig.@general[0].nodes_in_network=11_to_100
uci set wireless.radio0.distance=10
uci set wireless.radio0.dynamic_txpower=0
uci set wireless.radio0.dynamic_txpower_aggr=0
uci set wireless.radio0.txpower=17
uci set hotspot-wizard.@general[0].command=’-n simpleconfig -k DoodleSmartRadio -tpc 10 -atpc 0 -c 12 -b 26 -ht40 0 -d 10 -e true -a client_enabled -nn 11_to_100 -emv 0 -msvlan 160 --mesh-iface usb0 --mesh-iface eth0 mesh ap_no_fes’
uci commit
/etc/init.d/network restart

