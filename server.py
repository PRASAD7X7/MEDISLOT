from app import PORT, run


if __name__ == "__main__":
    print(f"MediSlot running at http://127.0.0.1:{PORT}")
    print("Starting the merged Flask application.")
    run()
