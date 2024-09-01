def bgr_to_hex(rgb):
    rgb_str = '%02x%02x%02x' % rgb
    return "#" + rgb_str[4:] + rgb_str[2:4] + rgb_str[:2]

def hex_to_bgr(hex_color):
    if hex_color.startswith('#'):
        hex_color = hex_color[1:]
        
    return tuple(int(hex_color[i:i+2], 16) for i in (4, 2, 0))
    
