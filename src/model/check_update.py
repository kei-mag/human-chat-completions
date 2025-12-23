import re
from logging import getLogger

import httpx

from __version__ import VERSION

logger = getLogger(__name__)

client = httpx.AsyncClient()
current = VERSION


async def check_update_available():
    try:
        res = await client.get(
            "https://api.github.com/repos/miyamoto-hai-lab/human-chat-completions/releases",
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "miyamoto-hai-lab/human-chat-completions update-checker",
            },
            timeout=30,
            follow_redirects=True,
        )
        if res.status_code == 200:
            latest = sorted(res.json(), key=lambda d: d["published_at"], reverse=True)[
                0
            ]["tag_name"].lstrip("v")
            return version_parse(latest) > version_parse(current), current, latest
        else:
            return False, current, "unknown"
    except Exception as e:
        logger.exception(e)
        return False, current, "unknown"


def version_parse(text):
    """バージョンを不等号で比較可能なタプルにして返す"""

    # 数字または単語で分割
    version_split = re.findall(r"\d+|[a-zA-Z]+", text)

    # 頭にversionなどがついていたら除去
    prefix = ["v", "ver", "version", "vol"]
    if version_split[0].lower() in prefix:
        version_split = version_split[1:]

    # プレリリースを表す文字列
    prerelease_str = ["a", "alpha", "b", "beta", "canary", "rc", "pre", "preview"]

    output = []

    for item in version_split:
        if item.isdecimal():
            output.append((int(item), ""))
        elif item.lower() in prerelease_str:
            output.append((-1, item))
        else:
            output.append((0, item))

    # 末尾に0を追加することでプレリリースと比較できるようにする
    output.append((0, ""))

    return tuple(output)
