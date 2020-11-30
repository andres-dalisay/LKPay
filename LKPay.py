#!/usr/bin/env python
#A few parts of this code was adapted from this RFID Attendance System by Emmet Young of PiMyLifeUp: https://pimylifeup.com/raspberry-pi-rfid-attendance-system/
#test
import sys, time, RPi.GPIO as GPIO, mysql.connector, board, digitalio, adafruit_character_lcd.character_lcd as LCD, curses
from mfrc522 import SimpleMFRC522

db = mysql.connector.connect(
    host="localhost",
    user="lkpayadmin",
    passwd="meridian",
    database="lkpay"
)


cur = db.cursor()
reader = SimpleMFRC522()

lcd_rs = digitalio.DigitalInOut(board.D4)
lcd_en = digitalio.DigitalInOut(board.D24)
lcd_d7 = digitalio.DigitalInOut(board.D22)
lcd_d6 = digitalio.DigitalInOut(board.D18)
lcd_d5 = digitalio.DigitalInOut(board.D17)
lcd_d4 = digitalio.DigitalInOut(board.D23)
lcd_columns = 16
lcd_rows = 2
lcd = LCD.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows)

def input_c(message):
    try:
        win = curses.initscr()
        win.addstr(0, 0, message)
        while True: 
            ch = win.getch()
            if ch in range(32, 127): 
                break
            time.sleep(0.05)
    finally:
        curses.endwin()
    return chr(ch)

def pay():
    try:
        lcd.clear()
        lcd.message = "Input payment\namount:"
        lcd.blink = True
        payment_amount = float(input("Input payment amount:"))
        assert(payment_amount > 0)
        lcd.blink = False
        
        lcd.clear()
        lcd.message = "P" + str(payment_amount) + " payment.\nProceed? 1 = Yes"
        print("P", payment_amount, "is the amount for payment.")
        c = input_c("Proceed with payment? (1 is Yes): ")
        
        if c == "1":
            try:
                lcd.clear()
                lcd.message = "Place ID card to\ncash-in."
                print("Place ID card to cash-in.")
                rfid_uid, text = reader.read()
                time.sleep(0.5)
                
                
                cur.execute("SELECT name, bal FROM Accounts WHERE rfid_uid =" + str(rfid_uid))
                name, c_total_bal = cur.fetchone()
                
                if c_total_bal < payment_amount:
                    print("Error: Insufficient balance. Need P" + str(float(payment_amount) - float(c_total_bal)) + " more.")
                    lcd.clear()
                    lcd.message = "Insufficient\nbalance."
                    time.sleep(1)
                    lcd.clear()
                    lcd.message = "Need \nP" + str(float(payment_amount) - float(c_total_bal)) + " more."
                    time.sleep(2.5)
                    
                else:
                    cur.execute("UPDATE Accounts SET bal=bal-" + str(payment_amount) + " WHERE rfid_uid=" + str(rfid_uid))
                    cur.execute("INSERT INTO Transactions(rfid_uid, trans_amt, acct_netbal) SELECT rfid_uid, -" + str(payment_amount) + ", " + str(c_total_bal) + " FROM Accounts WHERE rfid_uid=" + str(rfid_uid))
                    db.commit()
                    
                    cur.execute("SELECT bal FROM Accounts WHERE rfid_uid =" + str(rfid_uid))
                    c_total_bal = cur.fetchone()
                    
                    time.sleep(1)
                    
                    print ("Deducted P" + str(payment_amount) + " from " + str(name) + ". Remaining balance is P" + str(c_total_bal[0]) + ".")
                    lcd.clear()
                    lcd.message = "-P" + str(payment_amount) + " from\n" + str(name)
                    time.sleep(2)            
                    lcd.clear()
                    lcd.message = "Remaining bal:\nP" + str(c_total_bal[0])
                    time.sleep(2.5)
                
            finally:
                print()
        
        else:
            print("Payment cancelled.")
            lcd.clear()
            lcd.message = "Payment \ncancelled."
            time.sleep(1.5)
    except:
        print("\nAn exception has occured Please try again.")
        lcd.clear()
        lcd.message = "Excptn occured.\nPlease try again."
        time.sleep(1)
            
def cash_in():
    try:
        lcd.clear()
        lcd.message = "Input reload\namount:"
        lcd.blink = True
        reload_amount = float(input("Input reload amount: "))
        assert(reload_amount > 0)
        lcd.blink = False
        
        lcd.clear()
        lcd.message = "P" + str(reload_amount) + " cash-in.\nProceed? 1 = Yes"
        print("P", reload_amount, "will be added to the customer")
        c = input_c("Proceed with cash-in? (1 is Yes): ")
        
        if c == "1":
            try:
                lcd.clear()
                lcd.message = "Place ID card to\ncash-in."
                print("Place ID card to cash-in.")
                rfid_uid, text = reader.read()
                time.sleep(0.5)
                
                cur.execute("UPDATE Accounts SET bal=bal+" + str(reload_amount) + " WHERE rfid_uid=" + str(rfid_uid))
                cur.execute("SELECT name, bal FROM Accounts WHERE rfid_uid =" + str(rfid_uid))
                name, c_total_bal = cur.fetchone()
                cur.execute("INSERT INTO Transactions(rfid_uid, trans_amt, acct_netbal) SELECT rfid_uid, " + str(reload_amount) + ", " + str(c_total_bal) + " FROM Accounts WHERE rfid_uid=" + str(rfid_uid))
                db.commit()
                
                time.sleep(1)
                
                print ("Added P" + str(reload_amount) + " to " + str(name) + ". Current balance is P" + str(c_total_bal) + ".")
                lcd.clear()
                lcd.message = "+P" + str(reload_amount) + " to\n" + str(name)
                time.sleep(2)            
                lcd.clear()
                lcd.message = "Current bal:\nP" + str(c_total_bal)
                time.sleep(2.5)
                
            finally:
                print()
        
    except:
        print("\nAn exception has occured Please try again.")
        lcd.clear()
        lcd.message = "Excptn occured.\nPlease try again."
        time.sleep(1)
            
def register():
    try:
        lcd.clear()
        lcd.message = "Proceed with\nreg? 1 = Yes"
        c = input_c("Proceed with registration? (1 is Yes): ")
        
        if c == "1":
            try:
                lcd.clear()
                lcd.message = "Place card to \nregister"
                print("Place ID card to register.")
                id, text = reader.read()
                time.sleep(0.5)
                
                cur.execute("SELECT id FROM Accounts WHERE rfid_uid=" + str(id))
                cur.fetchone()
                
                if cur.rowcount >= 1:
                    lcd.clear()
                    lcd.message = "Overwrite\nuser? (Y/N)"
                    print("Overwrite\nexisting user?")
                    overwrite = input_c("Overwrite (Y/N)? ")
                    
                    if overwrite[0] == "Y" or overwrite[0] == "y":
                        lcd.clear()
                        lcd.message = "Overwriting user."
                        print("Overwriting user.")
                        time.sleep(1)
                        sql_insert = "UPDATE Accounts SET name = %s WHERE rfid_uid=%s"
                        
                        lcd.clear()
                        lcd.message = "Enter new name"
                        print("Enter new name")
                        new_name = input("Name: ")
                        
                        cur.execute(sql_insert, (new_name, id))
                        db.commit()

                        lcd.clear()
                        lcd.message = "User saved:\n<" + new_name + ">"
                        print("User <" + new_name + "> Saved")
                        time.sleep(2.5)
                        
                    elif overwrite[0] == "N" or overwrite[0] == "n":
                        lcd.clear()
                        lcd.message = "Overwrite\ncancelled."
                        print("Overwrite cancelled.")
                        time.sleep(1)
                        
                else:
                    sql_insert = "INSERT INTO Accounts (name, rfid_uid, bal) VALUES (%s, %s, 0.0)"
                
                    lcd.clear()
                    lcd.message = "Enter new name"
                    print("Enter new name")
                    new_name = input("Name: ")
                    
                    cur.execute(sql_insert, (new_name, id))
                    db.commit()

                    lcd.clear()
                    lcd.message = "User saved:\n<" + new_name + ">"
                    print("User <" + new_name + "> Saved")
                    time.sleep(2.5)
            
            finally:
                print()
        else:
            print('Registration cancelled.')
            lcd.clear()
            lcd.message = 'Registration \ncancelled.'
            time.sleep(1.5)
    except:
        print("\nAn exception has occured Please try again.")
        lcd.clear()
        lcd.message = "Excptn occured.\nPlease try again."
        time.sleep(1)

def checkbal():
    try:
        lcd.clear()
        lcd.message = "Place card to\ncheck balance"
        print("Place ID card to check balance.")        
        id, text = reader.read()
        
        time.sleep(0.5)
        
        cur.execute("SELECT bal FROM Accounts WHERE rfid_uid=" + str(id))
        bal = cur.fetchone()
        cur.execute("SELECT name FROM Accounts WHERE rfid_uid=" + str(id))
        name = cur.fetchone()
        print(str(name[0]) + ":\nP" + str(bal[0]))
        lcd.clear()
        lcd.message = str(name[0]) + ":\nP" + str(bal[0])
        
        time.sleep(2.5)
    
    except:
        print("\nAn exception has occured Please try again.")
        lcd.clear()
        lcd.message = "Excptn occured.\nPlease try again."
        time.sleep(1)
        
    finally:
        print()
    
while True:
    lcd.clear()
    lcd.message = "1     2      3 \nPay   Load   Bal"
    c = input_c("Select operation.\n1. Payment\n2. Load\n3. Check Balance\n0. Register (Keyboard required to input name!)\nEnter choice (1/2/3/4): ")
    try:
        if c == "1":
            pay()

        elif c == "2":
            cash_in()

        elif c == "3":
            checkbal()
        
        elif c == "0":
            register()     
        else:
            print("Invalid input")

    except:
        print("\nAn exception has occured Please try again.")
        lcd.clear()
        lcd.message = "Excptn occured.\nPlease try again."
        time.sleep(1)
        
    finally:    
        print("-----------------\n")
