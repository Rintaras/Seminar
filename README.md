サーバーの起動
go run main.go


ポート番号からプロセスを探すして、サーバー停止。
lsof -i :3000  # プロセスIDを確認
kill <プロセスID>