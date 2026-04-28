if __name__ == "__main__":
    try:
        import checker
        checker.main()
    except KeyboardInterrupt:
        # Want no traceback.
        print("Bye-bye.")
