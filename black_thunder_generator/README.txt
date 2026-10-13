ブラックサンダー 静的HTML生成ツール

1. ZIPを展開します。
2. generate.py を、GitHubリポジトリの black-thunder 内（index.html と同じ場所）に置きます。
3. 同じ場所に json/ json2/ json3/ json4/ フォルダがあることを確認します。
4. Python 3.9以上で `python generate.py` を実行します。
5. products/ フォルダと sitemap.xml が生成されます。
6. 内容を確認してから GitHub にアップロードしてください。

重要：このツールは index.html と product.html を変更しません。
現在の sitemap.xml は上書きします。実行前にバックアップしてください。
静的ページへのリンクを一覧に追加する変更はまだ行っていません。
生成ページは現在の product.html と似たレイアウトですが完全な同一デザインではありません。
画像は元の imag/ フォルダにある前提です。
