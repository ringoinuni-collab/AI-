from sentence_transformers import SentenceTransformer
from sentence_transformers import util
from re import search

# 日本語対応モデル
model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# コマンドと、それぞれの代表的な文章
commands = {
    "UP_VOLUME": [
        "音量を上げて",
        "ボリュームを大きくして",
        "音をちょっと大きくして",
        "音を一気に上げて",
        "音量を少し大きくしてください",
        "もっと大きくして"
    ],
    "DOWN_VOLUME": [
        "音量を下げて",
        "ボリュームを小さくして",
        "音を弱めて",
        "音を一気に下げて",
        "音量を少し小さくしてください",
        "もうちょっと小さくして"
    ],
}

# 登録文章をベクトル化
command_texts = []
command_names = []

for command, sentences in commands.items():
    for sentence in sentences:
        command_texts.append(sentence)
        command_names.append(command)

command_embeddings = model.encode(
    command_texts,
    convert_to_tensor=True
)

LEVELS = {
    "ちょっと": 3,
    "少し": 3,
    "そこそこ": 5,
    "かなり": 10,
    "結構": 10,
    "だいぶ": 10,
    "大分": 10,
    "しっかり": 10,
    "大幅に": 15,
    "一気に": 15,
    "思い切り": 25,
    "思いっきり": 25,
}

def recognize_command(text) -> float:
    # 入力文章をベクトル化
    input_embedding = model.encode(
        text,
        convert_to_tensor=True
    )

    # 類似度を計算
    scores = util.cos_sim(
        input_embedding,
        command_embeddings
    )[0]

    # 最も類似度が高い文章を取得
    best_index = scores.argmax().item()
    best_score = scores[best_index].item()

    # 閾値を設定
    if best_score < 0.65:
        return 0

    amount = extract_amount(text)

    return amount if "UP_VOLUME" == command_names[best_index] else -amount

def extract_amount(text):

    # 数値指定を優先
    match = search(
        r"(\d+(?:\.\d+)?)*(?:%|％|ポイント|パーセント|だけ)?",
        text
    )

    if match:
        return float(match.group(1))

    # 程度表現
    for word, amount in sorted(
        LEVELS.items(),
        key=lambda x: len(x[0]),
        reverse=True
    ):
        if word in text:
            return amount

    # デフォルト値
    return 5


if __name__ == "__main__":
    # テスト
    text = "明かりをつけてください"

    result = recognize_command(text)

    print(result)
