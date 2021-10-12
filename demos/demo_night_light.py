from pasco.code_node_device import CodeNodeDevice

def main():

    code_node = CodeNodeDevice()
    code_node.connect_by_id('123-456')

    while (code_node.read_data('Button1') == 0):
        if (code_node.read_data('Brightness') < 1):
            code_node.set_rgb_led(5,5,5)
        else:
            code_node.set_rgb_led(0,0,0)

if __name__ == "__main__":
    main()
