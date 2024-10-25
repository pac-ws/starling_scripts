#TMP_DIR=`mktemp -d`
#MAIN_DIR=${TMP_DIR}/main
#BUILD_DIR=${TMP_DIR}/build
#mkdir -p ${MAIN_DIR}
#mkdir -p ${BUILD_DIR}

InstallGeoGraphicLib () {
	echo "Setting up geographiclib"
	wget https://github.com/geographiclib/geographiclib/archive/refs/tags/v2.3.tar.gz -P ${MAIN_DIR}/src
	tar -xf ${MAIN_DIR}/src/v2.3.tar.gz -C ${MAIN_DIR}/src/
	tar -xf v2.3.tar.gz -C ${MAIN_DIR}/src/
	cmake -S ${MAIN_DIR}/src/geographiclib-2.3 -B ${BUILD_DIR}/geographiclib ${CMAKE_END_FLAGS} -DBUILD_SHARED_LIBS=OFF -DCMAKE_POSITION_INDEPENDENT_CODE=ON
	cmake --build ${BUILD_DIR}/geographiclib -j$(nproc)
	cmake --install ${BUILD_DIR}/geographiclib
	if [ $? -eq 0 ]; then
		echo "geographiclib install succeeded"
	else
		echo "geographiclib install failed"
		exit 1
	fi
}

InstallGeoGraphicLib

rm -rf ${TMP_DIR}
