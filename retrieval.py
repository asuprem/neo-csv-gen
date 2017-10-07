import operator
import time
from neo4j.v1 import GraphDatabase
import pdb
from synset_explorer import SynsetExplorer
from nltk.corpus import wordnet as wn
from nltk.corpus.reader.wordnet import WordNetError
from itertools import product
#import approximate_utils

uri = "bolt://localhost:7687"
driver = GraphDatabase.driver(uri, auth=("neo4j", "scientia"))

# RUN by python retrieval.py query1.query

def clauseJoin(matchClause,conditionClause,returnClause):
    return matchClause+' '+conditionClause+' '+returnClause

def sessionRun(clause):
    with driver.session() as session:
        result = session.run(clause)
    return result
def subject_relations_approximates(subjects):
    matchClause = 'match (n:aggregateObject)-[:SUBJ]->(r:aggregateRelation)'
    conditionClause = 'where n.synset in '+str(subjects)
    returnClause = 'return r'
    return sessionRun(clauseJoin(matchClause,conditionClause,returnClause))
def object_relations_approximates(objects):
    matchClause = 'match (r:aggregateRelation)-[:OBJ]->(o:aggregateObject)'
    conditionClause = 'where o.synset in '+str(objects)
    returnClause = 'return r'
    return sessionRun(clauseJoin(matchClause,conditionClause,returnClause))
def ssag_object_approximates(subjects,relations):
    matchClause = 'match (n:ssagObject)-[:SUBJ]->(r:ssagRelation)-[:OBJ]->(o:ssagObject)'
    conditionClause = 'where n.synset in '+str(subjects) +'and r.synset in ' + str(relations)
    returnClause = 'return o'
    return sessionRun(clauseJoin(matchClause,conditionClause,returnClause))

def generateRelations(gsubject,grelation,gobject):
    return list(product(gsubject,grelation,gobject))

def main():

    objectFamilies = SynsetExplorer('../ExtractedData/objects.db')
    relationFamilies = SynsetExplorer('../ExtractedData/relations.db')
    #query_file_name = sys.argv[1]
    query_file_name = 'queries/query2.query'
    query_file = open(query_file_name,'r')

    nouns = {}
    predicates = {}

    #Get the relations and nouns
    for line in query_file:
        line = line.strip().split(',')
        if line[1] == 'n':
            nouns[int(line[0])] = line[2]
        if line[1] == 'r':
            predicates[int(line[0])] = (line[2],int(line[3]), int(line[4]))
    
    relations = []
    for entry in predicates:
        relations.append((nouns[predicates[entry][1]],predicates[entry][0],nouns[predicates[entry][2]]))

    #----------------------------------------------------------------------------#
    # USE the relation component approximates to generate relation approximates
    queryApproximates={}
    for relation in relations:
        subjectFamily = objectFamilies.explore(relation[0])
        objectFamily = objectFamilies.explore(relation[2])
        predicateFamily = relationFamilies.explore(relation[1])

        start=time.time()
        #pdb.set_trace()
        result = subject_relations_approximates(subjectFamily.getBaseHypoRanking())
        aggregate_relation_subject = [item.values()[0]['synset'].encode("utf-8") for item in result]
        result = object_relations_approximates(objectFamily.getBaseHypoRanking())
        aggregate_relation_object = [item.values()[0]['synset'].encode("utf-8") for item in result]
        
        
        
        aggregate_relations = aggregate_relation_subject+aggregate_relation_object
        aggregate_relations = set([item for item in aggregate_relations if (item in aggregate_relation_subject and item in aggregate_relation_object)])
        aggregateSynsets = [wn.synset(item) for item in aggregate_relations]
        predicateSynsets = [wn.synset(item) for item in predicateFamily.getFullRanking()]
        
        #Set up the multiplicative factor here
        predicateCounts={}
        for item in predicateFamily.getFullRanking():
            predicateCounts[wn.synset(item)]= predicateFamily.getFamilySynsetCounts()[item] if item in predicateFamily.getFamilySynsetCounts() else predicateFamily.getTopLevelSynsetCounts()[item]
        predicateSum = float(sum([predicateCounts[item] for item in predicateCounts]))

        rankingAverages=[]
        #wuprankingAverages={}
        for item in aggregateSynsets:
            tSum = 0
            for mains in predicateSynsets:
                try:
                    tSum += item.wup_similarity(mains) * (predicateCounts[mains]/predicateSum)
                except WordNetError:
                    tSum += 0
                except TypeError:
                    tSum += 0
            #tSum=sum(tSum)/len(predicateCounts)
            rankingAverages.append((str(item)[8:-2],tSum))
        rankingAverages = sorted(rankingAverages,key=lambda x:x[1],reverse=True)
        finalRelationshipRanking = [item[0] for item in rankingAverages if item[1] >= (2./3)*rankingAverages[0][1]]
        
        # Mabe combine with hypo ranks????
        # we have finalRakings, subjectFamily.getBaseHypoRaking(), and objectFamily.getBaseHypoRanking()

        # We generate relations using base, first:
        queryApproximates[relation] = generateRelations(subjectFamily.getBaseRanking(), finalRelationshipRanking, objectFamily.getBaseRanking())

        
        
        
        #result = ssag_object_approximates(subjectFamily.getBaseHypoRanking(),aggregate_relation_subject)
        #ssag_objects = [item.values()[0]['synset'].encode("utf-8") for item in result]
        #print 'Finished getting ssag Objects in ' + str(time.time()-start)
    print 'Finished getting relations in ' + str(time.time()-start)
    pdb.set_trace()
        





    






if __name__ == "__main__":
    main()



'''

match (s:Object)-[:SUBJ]->(r:Relation)-[:OBJ]->(o:Object)
where s.synset="leg.n.01"
return s,r,o

'''
