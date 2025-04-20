from phone_controller import PhoneController

phone = PhoneController()
print("Test connexion avancé...")
print("Modèle:", phone.run_adb_command("getprop ro.product.model"))
print("Packages:", phone.run_adb_command("pm list packages")[:50] + "...")