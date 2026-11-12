
from .camera import run_camera


def main():

    print("==============================")
    print("  ⑥ 顔画像解析システム")
    print("==============================")

    try:
        run_camera(user_id="local_user")

    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
