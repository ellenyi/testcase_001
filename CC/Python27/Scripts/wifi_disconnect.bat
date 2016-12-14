CHCP 65001
netsh wlan disconnect interface="WIFI"
echo success
netsh wlan add profile filename="C:\Users\Administrator\WIFI-RXLT_2.4G.xml"
netsh wlan show profile
netsh wlan connect name="RXLT_2.4G" SSID="RXLT_2.4G" interface="WIFI"