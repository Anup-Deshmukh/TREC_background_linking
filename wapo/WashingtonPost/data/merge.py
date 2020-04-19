filenames = ['TREC_article_2012.txt', 'TREC_article_2013.txt', 'TREC_article_2014.txt', 'TREC_article_2015.txt'
, 'TREC_article_2016.txt', 'TREC_article_2017.txt', 'TREC_blog_2012.txt', 'TREC_blog_2013.txt', 'TREC_blog_2014.txt'
, 'TREC_blog_2015.txt', 'TREC_blog_2016.txt', 'TREC_blog_2017.txt'] 
  
with open('wapo_dataset_merged.txt', 'w') as outfile: 
  
    for names in filenames: 
        with open(names) as infile:           
            outfile.write(infile.read())