source ~daqowner/dist/etc/env.sh
newUHTRtool=/home/hep/dnoonan/newUHTRtool_HBHistogramming/hcal/hcalUHTR
export PATH=$newUHTRtool/bin/linux/x86_64_RedHat:/home/hep/ngFEC:$PATH

export LD_LIBRARY_PATH=$newUHTRtool/lib/linux/x86_64_RedHat/:/usr/lobal/lib:/home/hep/ChargeInjector/DAC/mcc-libhid_multDACs:$LD_LIBRARY_PATH
export PYTHONPATH=$ROOTSYS/lib:$PYTHONPATH

export IPBUS_MAP_PATH=/home/hep/dnoonan/map
