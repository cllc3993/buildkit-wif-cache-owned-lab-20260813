package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"time"

	actionscache "github.com/tonistiigi/go-actions-cache"
)

func main() {
	key := flag.String("key", "", "exact GitHub Actions cache key")
	out := flag.String("out", "cache-blob.bin", "output file")
	flag.Parse()
	if *key == "" {
		fmt.Fprintln(os.Stderr, "-key is required")
		os.Exit(2)
	}

	cache, err := actionscache.TryEnv(actionscache.Opt{Timeout: 2 * time.Minute})
	if err != nil {
		panic(err)
	}
	if cache == nil {
		panic("GitHub Actions cache runtime environment is unavailable")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()
	entry, err := cache.Load(ctx, *key)
	if err != nil {
		panic(err)
	}
	if entry == nil {
		fmt.Fprintln(os.Stderr, "cache key not visible to this workflow")
		os.Exit(3)
	}

	f, err := os.OpenFile(*out, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0o600)
	if err != nil {
		panic(err)
	}
	defer f.Close()
	if err := entry.WriteTo(ctx, f); err != nil {
		panic(err)
	}
	fmt.Printf("downloaded key %q to %s\n", *key, *out)
}
