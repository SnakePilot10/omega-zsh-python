#!/usr/bin/env python3
import sys
from src.ui.app import OmegaApp

def main():
    try:
        app = OmegaApp()
        app.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()