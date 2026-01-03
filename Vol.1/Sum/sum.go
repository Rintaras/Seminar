package main

import (
	"fmt"
	"os"
)

func main() {
	if len(os.Args) < 3 {
		fmt.Println("使い方: go run main.go <数値1> <数値2>")
		return
	}

	var a, b int
	fmt.Sscanf(os.Args[1], "%d", &a)
	fmt.Sscanf(os.Args[2], "%d", &b)
	fmt.Printf("%d + %d = %d\n", a, b, a+b)
	fmt.Printf("%d - %d = %d\n", a, b, a-b)
	fmt.Printf("%d * %d = %d\n", a, b, a*b)
	if b != 0 {
		fmt.Printf("%d / %d = %d\n", a, b, a/b)
	}
}
