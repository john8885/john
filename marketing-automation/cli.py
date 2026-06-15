"""커맨드라인 유틸 — 개별 자동화 작업 즉시 실행"""
import argparse
import sys


def cmd_post_instagram(args):
    from automation.instagram import post_photo, post_reel
    if args.type == "photo":
        pk = post_photo(args.file, args.caption)
        print(f"포스팅 완료: {pk}")
    else:
        pk = post_reel(args.file, args.caption, args.thumbnail)
        print(f"릴스 업로드 완료: {pk}")


def cmd_upload_youtube(args):
    from automation.youtube import upload_video, upload_shorts
    fn = upload_shorts if args.shorts else upload_video
    vid = fn(args.file, args.title, args.description, tags=args.tags.split(",") if args.tags else None)
    print(f"유튜브 업로드 완료: https://youtu.be/{vid}")


def cmd_send_email(args):
    from automation.email_sender import send_email
    ok = send_email([args.to], args.subject, args.body)
    print("발송 성공" if ok else "발송 실패")


def cmd_ad_report(args):
    import json
    from automation.ad_report import build_weekly_report
    report = build_weekly_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))


def cmd_crawl(args):
    import json
    from automation.crawler import crawl_naver_trending, crawl_keywords
    if args.mode == "trends":
        print(json.dumps(crawl_naver_trending(), ensure_ascii=False))
    else:
        print(json.dumps(crawl_keywords(args.keyword), ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="마케팅 자동화 CLI")
    sub = parser.add_subparsers(dest="command")

    # instagram
    ig = sub.add_parser("instagram", help="인스타그램 포스팅")
    ig.add_argument("--type", choices=["photo", "reel"], default="photo")
    ig.add_argument("--file", required=True)
    ig.add_argument("--caption", default="")
    ig.add_argument("--thumbnail")

    # youtube
    yt = sub.add_parser("youtube", help="유튜브 업로드")
    yt.add_argument("--file", required=True)
    yt.add_argument("--title", required=True)
    yt.add_argument("--description", default="")
    yt.add_argument("--tags", default="")
    yt.add_argument("--shorts", action="store_true")

    # email
    em = sub.add_parser("email", help="이메일 발송")
    em.add_argument("--to", required=True)
    em.add_argument("--subject", required=True)
    em.add_argument("--body", required=True)

    # ad-report
    sub.add_parser("ad-report", help="광고 리포트 출력")

    # crawl
    cr = sub.add_parser("crawl", help="데이터 크롤링")
    cr.add_argument("--mode", choices=["trends", "keyword"], default="trends")
    cr.add_argument("--keyword", default="")

    args = parser.parse_args()
    dispatch = {
        "instagram": cmd_post_instagram,
        "youtube": cmd_upload_youtube,
        "email": cmd_send_email,
        "ad-report": cmd_ad_report,
        "crawl": cmd_crawl,
    }
    if args.command in dispatch:
        dispatch[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
