# Data Observation
## Three rules:
* No wire service articles.  (That is, from Associated Press (AP), AFP, etc)
    * judge wire service articles as not relevant​
* No opinion or editorials.
    *  "Opinion", "Letters to the Editor", or "The Post's View" sections, as labeled in the "kicker" field, are​not relevant​.
* The list of links should be diverse.
    * not sure, waiting...


## Calculate
#### Level 1:
* fields:
    * id 595037
    * article_url 595037
    * title 595037
    * author 595037
    * published_date 595037
    * contents 595037
    * type 595037
    * source 595037
* type:
    * article 236649
    * blog 358388

#### Level 2:(Contents)
* About 414 examples contain 'null' element
* main fields:
    * type
        * kicker 566973 (news categories)
        * title 594527
        * byline 481012 (author)
        * date 595028
        * list 28241
        * deck 9402
        * tweet 170960
        * instagram 9868
        * video 596
        * image 1693
        * sanitized_html 11524  (may contain html tags such as: <a> )
        * pull_quote 29
        * inline_story 19
    * subtype
        * paragraph 11094325
        * subhead 180790 (subtitle, section)

#### Data Character
* There are 181 topics
* Paragraph
    * max length: 32905
    * median: 200+
    * min length: 0
* Sentence
    * max length: 12618
    * median: 200+
    * min length: 1
* Doc
    * max length: 78664
    * median: 2000+
    * min length: 1

## Processing
* Skip 'null' elements in Contents field
* Skip opinion or editorials file according to the "kicker" field.
    * `this would drop 23074 files`
* Only extract subtype="paragraph" in Contents
* Replace <.*?> with ""