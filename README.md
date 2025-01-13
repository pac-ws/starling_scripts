## Clone to starling
```
git clone https://github.com/pac-ws/starling_scripts.git /data/starling_scripts
```

## Install
```
export NAMESPACE=r0
cd /data/starling_scripts
bash setup-local.bash --ros ${NAMESPACE} --params --docker --offboard --disable-cams --pac ${NAMESPACE}
```

