[d-separation](https://www.probabilisticworld.com/conditional-dependence-independence/)

[Introduction to Bayesian Networks](https://towardsdatascience.com/introduction-to-bayesian-networks-81031eeed94e)
    - A Bayesian network is a directed acyclic graph in which each edge corresponds to a conditional dependency, and each node corresponds to a unique random variable. _Formally, if an edge (A, B) exists in the graph connecting random variables A and B, it means that P(B|A) is a factor in the joint probability distribution, so we must know P(B|A) for all values of B and A in order to conduct inference_.
    - Bayesian networks satisfy the __local Markov property__, which states that __a node is conditionally independent of its non-descendants given its parents__.
    - After simplification, the _joint distribution for a Bayesian network is equal to the product of P(node|parents(node)) for all nodes_
    - In order to calculate P(x, e), we must marginalize the joint probability distribution over the variables that do not appear in x or e, which we will denote as Y... Note that in larger networks, _Y will most likely be quite large_, since most inference tasks will only directly use a small subset of the variables. In cases like these, _exact inference as shown above is very computationally intensive_, so methods must be used to reduce the amount of computation. One more efficient method of exact inference is through variable elimination, which takes advantage of the fact that each factor only involves a small number of variables. This means that the _summations can be rearranged_ such that only factors involving a given variable are used in the marginalization of that variable. Alternatively, many networks are too large even for this method, so _approximate inference methods such as MCMC_ are instead used; these provide probability estimations that require significantly less computation than exact inference methods.

[What is the EM Algorithm?](https://www.statisticshowto.datasciencecentral.com/em-algorithm-expectation-maximization/)
    - The Expectation-Maximization (EM) algorithm is a way to _find maximum-likelihood estimates for model parameters when your data is incomplete, has missing data points, or has unobserved (hidden) latent variables. It is an iterative way to approximate the maximum likelihood function_.
    - The EM algorithm can very very slow, even on the fastest computer. It works best when you only have a small percentage of missing data and the dimensionality of the data isn’t too big. The higher the dimensionality, the slower the E-step; for data with larger dimensionality, you may find the E-step runs extremely slow as the procedure approaches a local maximum.

[What is the difference between a Bayesian network and an artificial neural network?](https://www.quora.com/What-is-the-difference-between-a-Bayesian-network-and-an-artificial-neural-network)
    Similarities
        - Both use directed graphs.
        - Both are used as classifier algorithms.
    Differences
        - In Bayesian networks the visual representation of graph that is vertices and edges have meaning- The network structure itself gives you valuable information about conditional dependence between the variables. With Neural Networks the network structure does not tell you anything.
        - Bayesian networks represent independence (and dependence) relationships between variables. Thus, the _links represent conditional relationships in the probabilistic sense_. Neural networks, generally speaking, have no such direct interpretation, and in fact the intermediate nodes of most neural networks are discovered features, instead of having any predicate associated with them in their own right.
        - Bayesian networks are generally simpler in comparison to Neural networks, with many decisions about hidden layers, and topology and variants.

[Bayesian Networks](https://ftp.cs.ucla.edu/pub/stat_ser/r277.pdf)
    - Perhaps the most important aspect of a Bayesian networks is that they are _direct representations of the world, not of reasoning processes. The arrows in the diagram represent real causal connections and not the flow of information during reasoning (as in rule-based systems and neural networks). Reasoning processes can operate on Bayesian networks by propagating information in any direction._

[BBN slide deck](https://www.saedsayad.com/docs/Bayesian_Belief_Network.pdf)

[pymc3](https://github.com/pymc-devs/pymc3)

[Variational Inference: Bayesian Neural Networks](https://docs.pymc.io/notebooks/bayesian_neural_network_advi.html)
    - One major drawback of sampling, however, is that it’s often very slow, especially for high-dimensional models. That’s why more recently, _variational inference_ algorithms have been developed that are almost as flexible as MCMC but much faster. Instead of drawing samples from the posterior, these algorithms instead fit a distribution (e.g. normal) to the posterior turning a sampling problem into and optimization problem. ADVI – Automatic Differentation Variational Inference – is implemented in PyMC3
    - _Neural Networks are extremely good non-linear function approximators and representation learners._
