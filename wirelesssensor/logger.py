#!/usr/bin/env python

import logging
import time
import struct
import serial as pyserial

from data import Session, Reading, Setpoint
from sqlalchemy import desc
log = logging.getLogger()

def standalone():
    db = Session()
    while True:
        try:
            log.info("Opening serial port")
            serial = pyserial.Serial('COM3', 115200, timeout=10) #/dev/ttyACM0
            log.info("Serial port open")

            while True:
                line = str(serial.readline(), 'ascii')
                if line:
                    (node_id, seq_no, reading_type, temperature,
                     checksum_sent, checksum_calc) = line.split(" ")
                    reading = Reading()
                    reading.node_id = int(node_id)
                    reading.seq_no = int(seq_no)
                    reading.reading_type = reading_type
                    reading.reading = float(temperature)
                    reading.checksum_sent = int(checksum_sent, 16)
                    reading.checksum_calc = int(checksum_calc, 16)
                    db.add(reading)
                    db.commit()
                    log.info("Read line: %r", line)         
                    
                    setpoint = db.query(Setpoint).filter(Setpoint.zone_id == reading.node_id).order_by(desc(Setpoint.created_at)).first()
                    if setpoint is not None:
                        log.info("actual temp %s desired temp %s" % (reading.reading, setpoint.temperature))
                        if setpoint.temperature > reading.reading:
                            serial.write(struct.pack('!B', (reading.node_id << 1))) # flip that zone to on
                            log.info("opening zone %s" % reading.node_id)
                        else:
                            serial.write(struct.pack('!B', (reading.node_id << 1) + 1)) # flip that zone to off
                            log.info("closing zone %s" % reading.node_id)


        except Exception:
            log.exception("Exception")
            time.sleep(20)


def main():
    logging.basicConfig(level=logging.DEBUG)
    standalone()

if __name__ == "__main__":
    main()
