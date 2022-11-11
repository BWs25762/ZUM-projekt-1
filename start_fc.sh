modprobe -r ec_sys
modprobe ec_sys write_support=1
python src/main.py
