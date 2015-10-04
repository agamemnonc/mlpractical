
# Machine Learning Practical (INFR11119),
# Pawel Swietojanski, University of Edinburgh

import cPickle
import gzip
import numpy
import os
import cv


class DataProvider(object):
    """
    Data provider defines an interface for our
    generic data-independent readers.
    """
    def __init__(self, batch_size, randomize=True):
        """
        :param batch_size: int, specifies the number
               of elements returned at each step
        :param randomize: bool, shuffles examples prior
               to iteration, so they are presented in random
               order for stochastic gradient descent training
        :return:
        """
        self.batch_size = batch_size
        self.randomize = randomize
        self._curr_idx = 0

    def reset(self):
        """
        Resets the provider to the initial state to
        use in another epoch
        :return: None
        """
        self._curr_idx = 0

    def __randomize(self):
        """
        Data-specific implementation of shuffling mechanism
        :return:
        """
        raise NotImplementedError()

    def __iter__(self):
        return self

    def next(self):
        """
        Data-specific iteration mechanism.
        :return:
        """
        raise NotImplementedError()


class MNISTDataProvider(DataProvider):
    """
    The class iterates over MNIST digits dataset, in possibly
    random order.
    """
    #max_num_examples is the total number of examples across batches.
    def __init__(self, dset,
                 batch_size=10,
                 max_num_examples=-1,
                 randomize=True):

        super(MNISTDataProvider, self).\
            __init__(batch_size, randomize)

        assert dset in ['train', 'valid', 'eval'], (
            "Expected dset to be either 'train', "
            "'valid' or 'eval' got %s" % dset
        )

        dset_path = './data/mnist_%s.pkl.gz' % dset
        assert os.path.isfile(dset_path), (
            "File %s was expected to exist!." % dset_path
        )

        with gzip.open(dset_path) as f:
            x, t = cPickle.load(f)

        self._max_num_examples = max_num_examples
        self.x = x
        self.t = t
        self.num_classes = 10

        self._rand_idx = None
        if self.randomize:
            self._rand_idx = self.__randomize()

    def reset(self):
        super(MNISTDataProvider, self).reset()
        if self.randomize:
            self._rand_idx = self.__randomize()

    def __randomize(self):
        assert isinstance(self.x, numpy.ndarray)
        return numpy.random.permute(numpy.arange(0, self.x.shape[0]))

    def next(self):
        
        has_enough = (self._curr_idx + self.batch_size) <= self.x.shape[0]
        presented_max = (self._max_num_examples > 0 and
                         self._curr_idx + self.batch_size > self._max_num_examples)

        if not has_enough or presented_max:
            raise StopIteration()

        if self._rand_idx is not None:
            range_idx = \
                self._rand_idx[self._curr_idx:self._curr_idx + self.batch_size]
        else:
            range_idx = \
                numpy.arange(self._curr_idx, self._curr_idx + self.batch_size)

        rval_x = self.x[range_idx]
        rval_t = self.t[range_idx]
        rval_y = self.__to_one_of_k(rval_t)

        self._curr_idx += self.batch_size

        return rval_x, rval_y # Return 1-of-K encoding
        #return rval_x, rval_t

    def __to_one_of_k(self, rval_t):
        ook = numpy.zeros((self.num_classes,1), dtype = numpy.int8)
        ook[rval_t] = 1
        return ook
        
class METOfficeDataProvider(DataProvider):
    """
    The class iterates over MET Office data, in possibly
    random order.
    """
    #max_num_examples is the total number of examples across batches.
    def __init__(self, dset,
                 batch_size=10,
                 max_num_examples=-1,
                 randomize=True):

        super(MNISTDataProvider, self).\
            __init__(batch_size, randomize)

        data_meteo_raw = [];
        with open('./data/HadSSP_daily_qc.txt', 'rb') as csvfile:
            data_meteo_reader = csv.reader(csvfile, delimiter=' ', quotechar='|', skipinitialspace=True)
            for row in data_meteo_reader:
                data_meteo_raw.append(row)
        
        # Get rid of empty elements
        for ii in range(numpy.shape(data_meteo)[0]):
            data_meteo[ii] = filter(None, data_meteo[ii])
            
        # Get rid of headers
        data_meteo = data_meteo[3:]
        
        # Convert to numpy array
        data_meteo_np = numpy.array(data_meteo)
        
        
        self._max_num_examples = max_num_examples
        self.x = x
        self.t = t
        self.num_classes = 10

        self._rand_idx = None
        if self.randomize:
            self._rand_idx = self.__randomize()

    def reset(self):
        super(MNISTDataProvider, self).reset()
        if self.randomize:
            self._rand_idx = self.__randomize()

    def __randomize(self):
        assert isinstance(self.x, numpy.ndarray)
        return numpy.random.permute(numpy.arange(0, self.x.shape[0]))

    def next(self):
        
        has_enough = (self._curr_idx + self.batch_size) <= self.x.shape[0]
        presented_max = (self._max_num_examples > 0 and
                         self._curr_idx + self.batch_size > self._max_num_examples)

        if not has_enough or presented_max:
            raise StopIteration()

        if self._rand_idx is not None:
            range_idx = \
                self._rand_idx[self._curr_idx:self._curr_idx + self.batch_size]
        else:
            range_idx = \
                numpy.arange(self._curr_idx, self._curr_idx + self.batch_size)

        rval_x = self.x[range_idx]
        rval_t = self.t[range_idx]
        rval_y = self.__to_one_of_k(rval_t)

        self._curr_idx += self.batch_size

        return rval_x, rval_y # Return 1-of-K encoding

class FuncDataProvider(DataProvider):
    """
    Function gets as an argument a list of functions random samples
    drawn from normal distribution which means are defined by those
    functions.
    """
    def __init__(self,
                 fn_list=[lambda x: x ** 2, lambda x: numpy.sin(x)],
                 std_list=[0.1, 0.1],
                 x_from = 0.0,
                 x_to = 1.0,
                 points_per_fn=200,
                 batch_size=10,
                 randomize=True):

        super(FuncDataProvider, self).__init__(batch_size, randomize)

        def sample_points(y, std):
            ys = numpy.zeros_like(y)
            for i in xrange(y.shape[0]):
                ys[i] = numpy.random.normal(y[i], std)
            return ys

        x = numpy.linspace(x_from, x_to, points_per_fn, dtype=numpy.float32)
        means = [fn(x) for fn in fn_list]
        y = [sample_points(mean, std) for mean, std in zip(means, std_list)]

        self.x_orig = x
        self.y_class = y

        self.x = numpy.concatenate([x for ys in y])
        self.y = numpy.concatenate([ys for ys in y])

        if self.randomize:
            self._rand_idx = self.__randomize()
        else:
            self._rand_idx = None

    def __randomize(self):
        assert isinstance(self.x, numpy.ndarray)
        return numpy.random.permute(numpy.arange(0, self.x.shape[0]))

    def __iter__(self):
        return self

    def next(self):
        if (self._curr_idx + self.batch_size) >= self.x.shape[0]:
            raise StopIteration()

        if self._rand_idx is not None:
            range_idx = self._rand_idx[self._curr_idx:self._curr_idx + self.batch_size]
        else:
            range_idx = numpy.arange(self._curr_idx, self._curr_idx + self.batch_size)

        x = self.x[range_idx]
        y = self.y[range_idx]

        self._curr_idx += self.batch_size

        return x, y

