## サーバーの起動
サーバーを起動するには、以下のコマンドを実行します：

```bash
go run main.go (任意のファイル名)
```

## サーバーの停止

ポート番号からプロセスを探して、サーバーを停止します：

```bash
# プロセスIDを確認
lsof -i :3000

# プロセスを停止
kill <プロセスID>
```

### ワンライナーで停止する場合

```bash
kill $(lsof -t -i :3000)
```

## quic-goパッケージの取得

パッケージをインストールするには、以下のコマンドを実行します：

```bash
go get github.com/quic-go/quic-go
```

### 参考資料

- [quic-goサーバーの実装例](https://qiita.com/mochi_2225/items/3a3d37b403f3b7a5c46d)