# Reject patches to ESP-IDF
./build.sh -I v4.4.4 -A release/v2.0.9 -t esp32s3 -b idf_libs 80m qio
./build.sh -I v4.4.4 -A release/v2.0.9 -t esp32s3 -b copy_bootloader 80m qio
cp -r ./extras/*  ./out/tools/sdk/esp32s3/

rm -rf ~/.arduino15/packages/esp32/hardware/esp32/2.0.9/tools/sdk/esp32s3
mkdir ~/.arduino15/packages/esp32/hardware/esp32/2.0.9/tools/sdk/esp32s3
cp -r ./out/tools/sdk/esp32s3/* ~/.arduino15/packages/esp32/hardware/esp32/2.0.9/tools/sdk/esp32s3


rm -rf ~/.platformio/packages/framework-arduinoespressif32/tools/sdk/esp32s3
mkdir ~/.platformio/packages/framework-arduinoespressif32/tools/sdk/esp32s3
cp -r ./out/tools/sdk/esp32s3/* ~/.platformio/packages/framework-arduinoespressif32/tools/sdk/esp32s3
