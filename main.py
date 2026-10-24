import sys

from app import RestaurantApp
from app.utils import feedback
from app.utils.exceptions import AppError


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    try:
        RestaurantApp().run()
    except (KeyboardInterrupt, EOFError):
        print()
        feedback.info("Program closed.")
    except AppError as error:
        feedback.error(str(error))
        sys.exit(1)


if __name__ == "__main__":
    main()
