import SPTAG

from ..base.module import BaseANN


class Sptag(BaseANN):
    def __init__(self, metric, selectHead):
        self._selectHead = str(selectHead)
        self._metric = {"angular": "Cosine", "euclidean": "L2"}[metric]

    def fit(self, X):
        self._sptag = SPTAG.AnnIndex('SPANN', "Float", X.shape[1])

        # Set the thread number to speed up the build procedure in parallel 
        self._sptag.SetBuildParam("IndexAlgoType", "BKT", "Base")
        self._sptag.SetBuildParam("IndexDirectory", "spann_index", "Base")
        self._sptag.SetBuildParam("DistCalcMethod", "L2", "Base")

        self._sptag.SetBuildParam("isExecute", "true", "SelectHead")
        self._sptag.SetBuildParam("NumberOfThreads", "32", "SelectHead")
        self._sptag.SetBuildParam("Ratio", "0.2", "SelectHead") # index.SetBuildParam("Count", "200", "SelectHead")
        self._sptag.SetBuildParam("SelectHeadType", self._selectHead, "SelectHead")

        self._sptag.SetBuildParam("isExecute", "true", "BuildHead")
        self._sptag.SetBuildParam("RefineIterations", "3", "BuildHead")
        self._sptag.SetBuildParam("NumberOfThreads", "32", "BuildHead")

        self._sptag.SetBuildParam("isExecute", "true", "BuildSSDIndex")
        self._sptag.SetBuildParam("BuildSsdIndex", "true", "BuildSSDIndex")
        self._sptag.SetBuildParam("PostingPageLimit", "12", "BuildSSDIndex")
        self._sptag.SetBuildParam("SearchPostingPageLimit", "12", "BuildSSDIndex")
        self._sptag.SetBuildParam("NumberOfThreads", "32", "BuildSSDIndex")
        self._sptag.SetBuildParam("InternalResultNum", "32", "BuildSSDIndex")
        self._sptag.SetBuildParam("SearchInternalResultNum", "64", "BuildSSDIndex")

        self._sptag.Build(X, X.shape[0], False)

    def set_query_arguments(self, MaxCheck, InternalResultNum, SearchInternalResultNum):
        self._maxCheck = MaxCheck
        self._internalResultNum = InternalResultNum
        self._searchInternalResultNum = SearchInternalResultNum
        self._sptag.SetSearchParam("MaxCheck", str(self._maxCheck), "BuildHead")
        self._sptag.SetSearchParam("MaxCheck", str(self._maxCheck), "BuildSSDIndex")
        self._sptag.SetSearchParam("InternalResultNum", str(self._internalResultNum), "BuildSSDIndex")
        self._sptag.SetSearchParam("SearchInternalResultNum", str(self._searchInternalResultNum), "BuildSSDIndex")

    def query(self, v, k):
        return self._sptag.Search(v, k)[0]

    def __str__(self):
        return "Sptag(metric=%s, selectHead=%s, check=%d, InternalResultNum=%d, SearchInternalResultNum=%d)" % (self._metric, self._selectHead, self._maxCheck, self._internalResultNum, self._searchInternalResultNum)
