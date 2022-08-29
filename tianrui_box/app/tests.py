from multiprocessing import shared_memory
shm_a = shared_memory.SharedMemory(create=True, size=2)
# type(shm_a.buf)

# buffer = shm_a.buf
# len(buffer)

# buffer[:4] = bytearray([22, 33, 44, 55])  # Modify multiple at once
# buffer[4] = 100                           # Modify single byte at a time
# # Attach to an existing shared memory block
# shm_b = shared_memory.SharedMemory(shm_a.name)
# import array
# array.array('b', shm_b.buf[:5])  # Copy the data into a new array.array

shm_a.buf[:2] = b'g1'  # Modify via shm_b using bytes
shm_a.buf.tolist()
shm_a.buf.tobytes()
print(bytes(shm_a.buf[:2]))      # Access via shm_a
shm_a.buf[1] = 100
print(shm_a.buf[1])
# shm_b.close()   # Close each SharedMemory instance
print(bytes(shm_a.buf[:2]))
shm_a.close()
shm_a.unlink()  # Call unlink only once to release the shared memory