filenames = ['TREC_article_2012.txt', 'TREC_article_2013.txt', 'TREC_article_2014.txt', 'TREC_article_2015.txt'
, 'TREC_article_2016.txt', 'TREC_article_2017.txt', 'TREC_blog_2012.txt', 'TREC_blog_2013.txt', 'TREC_blog_2014.txt'
, 'TREC_blog_2015.txt', 'TREC_blog_2016.txt', 'TREC_blog_2017.txt'] 

#filenames = ['1.txt', '2.txt']
  
with open('wapo_dataset_merged.txt', 'w') as outfile: 
#with open('3.txt', 'w') as outfile: 
   
    for names in filenames: 
        with open(names) as infile:           
<<<<<<< Updated upstream
            outfile.write(infile.read())
=======
            outfile.write(infile.read()) 
        #outfile.write("\n") 
>>>>>>> Stashed changes
