"""
ClassOS LCD Service Package

Drives a 20x4 I2C Character LCD (HD44780 + PCF8574 backpack)
connected to the Raspberry Pi 5 GPIO I2C pins.

Falls back gracefully to console logging on non-Pi hardware
or when LCD_ENABLED=false.
"""
