import requests

from pasco_ble import PASCOBLEDevice

def main():
    # Connect to PASCO Device
    device = PASCOBLEDevice('//code.Node')

    while True:
        stock_list = ['AMC', 'TSLA', 'GME']

        for stock in stock_list:
            symbol=stock
            url = f'https://finnhub.io/api/v1/quote?symbol={symbol}&token=c3m6eg2ad3ic2eudae8g'
            r = requests.get(url)
            data = r.json()

            pct_change = round((data['c']/data['pc'] - 1) * 100)

            if pct_change > 0:
                device.code_node_set_rgb_leds(0, pct_change, 0)
            elif pct_change < 0:
                device.code_node_set_rgb_leds(abs(pct_change), 0, 0)
            else:
                device.code_node_set_rgb_leds(2, 2, 2)

            device.code_node_scroll_text(symbol)

if __name__ == "__main__":
    main()
