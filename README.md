# Control Pad

<img src="img/enclosure_render.png" alt="drawing" height="360"/>

Breaks out monitor controls into a desktop based keypad. Also runs a simple webserver on port 1602 to display text on
the screen from api requests.

<img src="img/webui.jpg" alt="drawing" height="360"/>

### Install

See Adafruit's guides to wiring
the [display](https://learn.adafruit.com/drive-a-16x2-lcd-directly-with-a-raspberry-pi/wiring) and
[keypad](https://learn.adafruit.com/matrix-keypad/python-circuitpython#python-computer-wiring-2998508) for details.\
Display pinout is defined in lines 10-18 of [display.py](display.py)\
Keypad pinout is defined in lines 35-36 of [keypad.py](keypad.py)

You'll likely need to get Monitor ID's are defined in [display.py](display.py) on lines 8-10\
These can be found using with `ddcutil` using\
 `ddcutil capabilities | awk '/Feature: 60 \(Input Source\)/{p=1} /^   Feature: 62/{p=0} p'`

```bash
git clone https://github.com/ChunkLightTuna/monitor_control.git 
cd monitor_control
sudo apt install ddcutil python-pip -y
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sed -e "s/\${DIR}/$(pwd | sed 's|/|\\\/|g')/g" monitor_control.sample.service > monitor_control.service
systemctl --user enable --now "$(pwd)/monitor_control.service"
```

### Parts List

- Raspberry Pi Zero W
- 1602 16x2 HD44780
- 4x4 Matrix Keypad
- 10K Trimpot
- Female/Female Jumper Wires
- Micro USB Cable
- Mini HDMI Cable

### Caveat Emptor

The matrix keypad scanning is hilariously inefficient. Half your CPU cycles will be devoted to this.
If this is unacceptable for your use case, consider a hardware based keypad decoder.