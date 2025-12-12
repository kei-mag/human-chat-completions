import socket
from contextlib import closing


def get_local_ip_for_server():
    """
    外部サーバーに接続を試みることにより、使用中のローカルIPアドレスを取得する
    """
    try:
        # UDPソケットを使用し、外部に出るためのルーティング情報を得る
        with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as s:
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
    except socket.error:
        # エラー時はデフォルトとして localhost を返すなど
        return '127.0.0.1'

print(get_local_ip_for_server())
