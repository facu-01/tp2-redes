# librerias
import serial
import time

# Funciones

# Implementacion codigo CRC para deteccion de errores.
# XOR para la division de binarios.
def xor(a, b):
    # inicializar resultado
    result = []

    # Recorrer todos los bits, si los bits son iguales, entonces XOR es 0, si no 1
    for i in range(1, len(b)):
        if a[i] == b[i]:
            result.append('0')
        else:
            result.append('1')

    return ''.join(result)


# Realiza la división Modulo-2
def mod2div(divident, divisor):
    # Número de bits que se deben XORear a la vez.
    pick = len(divisor)

    # Cortar el dividendo a la longitud adecuada para cada paso
    tmp = divident[0:pick]

    while pick < len(divident):
        if tmp[0] == '1':
            # sustituir el dividendo por el resultado de XOR y tirar 1 bit hacia abajo
            tmp = xor(divisor, tmp) + divident[pick]
        else:  # Si el bit más a la izquierda es '0'
            tmp = xor('0' * pick, tmp) + divident[pick]

        # incremento pick para avanzar
        pick += 1

    # Para los últimos n bits, tenemos que llevarlo a cabo normalmente
    if tmp[0] == '1':
        tmp = xor(divisor, tmp)
    else:
        tmp = xor('0' * pick, tmp)

    checkword = tmp
    return checkword


# Función utilizada en el lado del emisor para codificar
# datos con CRC añadiendo el resto de la división modular
# al final de los datos.
def encodeData(data, key):
    l_key = len(key)

    # Appends n-1 zeroes at end of data
    appended_data = data + '0' * (l_key - 1)
    remainder = mod2div(appended_data, key)

    # Append remainder in the original data
    codeword = data + remainder
    return codeword


# Función utilizada en el lado del receptor 
# para decodificar el CRC y los datos recibidos por el emisor
def decodeData(data, key):
    l_key = len(key)

    # Appends n-1 zeroes at end of data
    appended_data = data + '0' * (l_key - 1)
    remainder = mod2div(appended_data, key)

    return remainder


# Main - Desarrollo del ejercicio -------------------------------------------------------------

# puerto 2
puerto_2 = '/dev/pts/3'
# configuration serial port for COM2
baudrate = 19200
ser2 = serial.Serial(puerto_2, baudrate)
print('Puerto serial ' + ser2.name + ' abierto.')  # ver que el puerto se esté usando

# puerto 3
puerto_3 = '/dev/pts/4'
# configuration serial port for COM3
ser3 = serial.Serial(puerto_3, baudrate)
print('Puerto serial ' + ser3.name + ' abierto.')  # ver que el puerto se esté usando

resend_flag = 1 

while True:
    if resend_flag != -1:
        data = input("Ingrese comando o 'salir' :")

    # enmarcado - relleno de bytes
    if (data.find('$') != -1):
        # $ representa el ESC
        index = data.find('$')
        data = data[:index] + '$' + data[index:]
    if (data.find('&') != -1):
        # & representa la flag
        index = data.find('&')
        data = data[:index] + '$' + data[index:]

    marco = '&' + data + '&'

    if data == 'salir':
        ser2.close()
        ser3.close()
        exit()
    else:
        if resend_flag != -1:
            print('data ingresada con flags: ' + marco)
            marco_b = bin(int.from_bytes(marco.encode(), 'big'))
            print("data con flags en binario: " + marco_b)
            key = "1001"
            ans = encodeData(marco_b, key)  # encode crc
            print("Encoded data para ser enviada en binario : " + ans)

        # envia
        ser2.write(ans.encode())
        time.sleep(1)

        # Timer reenvio
        ack_espera_inicio = time.time()
        ack = ''
        
        # lee del buffer
        nro = ser3.inWaiting()
        out_encoded = ser3.read(nro)
        out = out_encoded.decode()
        print(nro,out_encoded,out)

        # testeando que llega el paquete entramado (en binario y con crc aplicado)
        print("Encoded data recibida en binario : " + out)

        # resuelve el crc el receptor del paquete.
        ansDecoded = decodeData(out, key)
        print("Resto CRC despues de decodificar -> " + ansDecoded)

        # Si el resto es todos ceros, no hay error.
        temp = "0" * (len(key) - 1)
        if ansDecoded == temp:
            print("Resto -> " + ansDecoded + " - NO ERROR FOUND.")
        else:
            print("ERROR DETECTADO en data")

        # convertimos de binario a ascii
        print('data a convertir a ascii ->' + out)
        # DECODIFICAR EL CRC
        final_data = False
        final_data = out[:-3]

        print(final_data)

        final_data = int(final_data, 2)
        final_data = final_data.to_bytes((final_data.bit_length() + 7) // 8, 'big').decode()
        print(final_data)

        # desenmarcado - relleno de bytes
        if (final_data.find('$') != -1):  # $ representa el ESC
            index = final_data.find('$')
            final_data = final_data[:index] + '' + final_data[index + 1:]
        if (final_data.find('&') != -1):  # & representa la flag
            final_data = final_data.replace('&', '')

        print(final_data)

        if (final_data):  # -----------comentar para no ack
            # envia acuse de recibo ack
            ser3.write(('ack').encode('utf-8'))  # -----------comentar para no ack

        ack_espera_fin = time.time()
        ack_espera_total = (ack_espera_fin - ack_espera_inicio)  # --------- comentar para version no ack

        if (ack_espera_total < 5.0):
            nro2 = ser2.inWaiting()
            ack = ser2.read(nro2)
            print(ack.decode('utf-8'))
            resend_flag = 1
        else:
            resend_flag = -1
            time.sleep(5)
            print('No se recibio ACK - Comienza reenvio de paquete.')
            time.sleep(1.5)

# Para version que no detecta el ACK: 
# Estan marcadas en el codigo
# comentar lineas -> 195,197,200
# descomentar lineas -> 201