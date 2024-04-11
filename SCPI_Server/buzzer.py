import RPi.GPIO as GPIO
import time
import sys

def parse_pwm_file(csv_file):
    final_pwm_list = []
    with open(csv_file) as my_file:
        for line in my_file:
            final_pwm_list.append([float(x) for x in line.split(',')])
    return final_pwm_list

def main(port_num, pwm_file):
    #port_num is usually 13
    leGPIOpwm = port_num

    final_pwm_list = parse_pwm_file(pwm_file)

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(leGPIOpwm, GPIO.OUT)
    pwm = GPIO.PWM(leGPIOpwm, 1000)
    pwm.start(0)

    pwm.ChangeDutyCycle(50)
    for cur_freq, cur_dur in final_pwm_list:
        if cur_freq == 0:
            cur_freq = 10000
            pwm.ChangeDutyCycle(0)
        else:
            pwm.ChangeDutyCycle(50)
        pwm.ChangeFrequency(cur_freq)
        time.sleep(cur_dur)

if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2])
