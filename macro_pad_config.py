import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk, messagebox
import keyboard

NUM_KEYS = 9
MAPPING_SIZE = 10

class MacroPadConfigurator:
    def __init__(self, root):
        self.root = root
        self.root.title("Macro Pad Configurator")
        self.root.geometry("400x400")
        self.serial_port = None
        self.device_list = []
        self.mappings = [''] * NUM_KEYS
        self.buttons = []

        self.create_main_menu()

    def create_main_menu(self):
        self.device_var = tk.StringVar()
        self.device_dropdown = ttk.Combobox(self.root, textvariable=self.device_var, width=30)
        self.device_dropdown.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        self.refresh_ports()

        refresh_button = tk.Button(self.root, text="🔄 Refresh", command=self.refresh_ports)
        refresh_button.grid(row=0, column=2, padx=5)

        connect_button = tk.Button(self.root, text="✔️ Connect", command=self.connect_to_device)
        connect_button.grid(row=1, column=0, padx=5, pady=5)

        self.program_button = tk.Button(self.root, text="📝 Program Buttons", command=self.show_program_ui, state=tk.DISABLED)
        self.program_button.grid(row=1, column=1, columnspan=2, padx=5, pady=5)

    def refresh_ports(self):
        try:
            self.device_list = serial.tools.list_ports.comports()
            display_names = [f"{p.device} - {p.description}" for p in self.device_list]
            self.device_dropdown['values'] = display_names
            if display_names:
                self.device_dropdown.current(0)
            else:
                self.device_dropdown.set("No devices found")
        except Exception as e:
            print("[Error] Refresh failed:", e)
            messagebox.showerror("Error", "Failed to list serial ports.")

    def connect_to_device(self):
        try:
            selection = self.device_dropdown.current()
            if selection == -1 or not self.device_list:
                messagebox.showerror("Error", "Please select a device.")
                return

            port = self.device_list[selection].device
            self.serial_port = serial.Serial(port, 9600, timeout=1)
            self.program_button.config(state=tk.NORMAL)
            messagebox.showinfo("Connected", f"Connected to {port}")
        except Exception as e:
            print("[Error] Could not open port:", e)
            self.serial_port = None
            messagebox.showerror("Connection Failed", str(e))

    def show_program_ui(self):
        for btn in self.buttons:
            btn.destroy()
        self.buttons.clear()

        for i in range(NUM_KEYS):
            btn = tk.Button(self.root, text=f"Key {i+1}", width=10, height=2,
                            command=lambda i=i: self.set_key(i))
            btn.grid(row=2 + i // 3, column=i % 3, padx=5, pady=5)
            self.buttons.append(btn)

        save_btn = tk.Button(self.root, text="💾 Save to Device", command=self.save_to_device)
        save_btn.grid(row=5, column=0, columnspan=3, pady=10)

    def set_key(self, index):
        popup = tk.Toplevel(self.root)
        popup.title(f"Assign Key for Button {index+1}")
        popup.geometry("300x150")
        popup.transient(self.root)
        popup.grab_set()

        label = tk.Label(popup, text="Press a key or shortcut")
        label.pack(pady=10)

        captured_var = tk.StringVar(value="None")
        captured_label = tk.Label(popup, textvariable=captured_var, font=("Arial", 12, "bold"))
        captured_label.pack(pady=5)

        confirmed = {'value': None}

        def on_key_event(e):
            try:
                combo = keyboard.get_hotkey_name().upper().replace(" ", "")
                captured_var.set(combo)
                confirmed['value'] = combo
            except:
                pass

        def confirm():
            if confirmed['value']:
                self.mappings[index] = confirmed['value'][:MAPPING_SIZE]
                self.buttons[index].configure(text=confirmed['value'][:MAPPING_SIZE])
            keyboard.unhook_all()
            popup.destroy()

        def cancel():
            confirmed['value'] = None
            keyboard.unhook_all()
            popup.destroy()

        btn_frame = tk.Frame(popup)
        btn_frame.pack(pady=10)

        ok_btn = tk.Button(btn_frame, text="OK", command=confirm, width=10)
        ok_btn.pack(side="left", padx=10)

        cancel_btn = tk.Button(btn_frame, text="Cancel", command=cancel, width=10)
        cancel_btn.pack(side="right", padx=10)

        keyboard.hook(on_key_event)

    def save_to_device(self):
        if not self.serial_port:
            messagebox.showerror("Error", "Device not connected.")
            return

        try:
            payload = "SET " + "|".join(self.mappings) + "\n"

            print("[Python] Sending:", repr(payload.strip()))
            self.serial_port.write(payload.encode())
            self.serial_port.flush()

            response_received = False
            print("[Python] Waiting for device response...")

            for i in range(10):
                try:
                    raw = self.serial_port.readline()
                    line = raw.decode(errors='ignore').strip()
                    if line:
                        print(f"[Arduino] → {line}")
                        if line == "OK":
                            response_received = True
                            break
                except Exception as decode_error:
                    print(f"[Decode error] → {decode_error}")
                    continue

            if response_received:
                messagebox.showinfo("Success", "Key mappings updated.")
            else:
                messagebox.showerror("Error", "Device did not confirm update. See console for details.")

        except Exception as e:
            print(f"[Fatal Error] → {e}")
            messagebox.showerror("Serial Error", str(e))


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = MacroPadConfigurator(root)
        root.mainloop()
    except Exception as e:
        print(f"[Startup Crash] → {e}")
