import cupy as cp


def trapz(y, x=None, dx=1.0, axis=-1):
    """
    Lifted from numpy
    https://github.com/numpy/numpy/blob/v1.15.1/numpy/lib/function_base.py#L3804-L3891

    Integrate along the given axis using the composite trapezoidal rule.
    Integrate `y` (`x`) along given axis.
    Parameters
    ----------
    y : array_like
        Input array to integrate.
    x : array_like, optional
        The sample points corresponding to the `y` values. If `x` is None,
        the sample points are assumed to be evenly spaced `dx` apart. The
        default is None.
    dx : scalar, optional
        The spacing between sample points when `x` is None. The default is 1.
    axis : int, optional
        The axis along which to integrate.
    Returns
    -------
    trapz : float
        Definite integral as approximated by trapezoidal rule.
    See Also
    --------
    sum, cumsum
    Notes
    -----
    Image [2]_ illustrates trapezoidal rule -- y-axis locations of points
    will be taken from `y` array, by default x-axis distances between
    points will be 1.0, alternatively they can be provided with `x` array
    or with `dx` scalar.  Return value will be equal to combined area under
    the red lines.
    References
    ----------
    .. [1] Wikipedia page: http://en.wikipedia.org/wiki/Trapezoidal_rule
    .. [2] Illustration image:
           http://en.wikipedia.org/wiki/File:Composite_trapezoidal_rule_illustration.png
    Examples
    --------
    >>> cp.trapz([1,2,3])
    4.0
    >>> cp.trapz([1,2,3], x=[4,6,8])
    8.0
    >>> cp.trapz([1,2,3], dx=2)
    8.0
    >>> a = cp.arange(6).reshape(2, 3)
    >>> a
    array([[0, 1, 2],
           [3, 4, 5]])
    >>> cp.trapz(a, axis=0)
    array([ 1.5,  2.5,  3.5])
    >>> cp.trapz(a, axis=1)
    array([ 2.,  8.])
    """
    y = cp.asanyarray(y)
    if x is None:
        d = dx
    else:
        x = cp.asanyarray(x)
        if x.ndim == 1:
            d = diff(x)
            # reshape to correct shape
            shape = [1]*y.ndim
            shape[axis] = d.shape[0]
            d = d.reshape(shape)
        else:
            d = diff(x, axis=axis)
    nd = y.ndim
    slice1 = [slice(None)]*nd
    slice2 = [slice(None)]*nd
    slice1[axis] = slice(1, None)
    slice2[axis] = slice(None, -1)
    try:
        ret = (d * (y[tuple(slice1)] + y[tuple(slice2)]) / 2.0).sum(axis)
    except ValueError:
        # Operations didn't work, cast to ndarray
        d = cp.asarray(d)
        y = cp.asarray(y)
        ret = add.reduce(d * (y[tuple(slice1)]+y[tuple(slice2)])/2.0, axis)
    return ret


def diff(a, n=1, axis=-1):
    """
    Calculate the n-th discrete difference along the given axis.
    The first difference is given by ``out[n] = a[n+1] - a[n]`` along
    the given axis, higher differences are calculated by using `diff`
    recursively.
    Parameters
    ----------
    a : array_like
        Input array
    n : int, optional
        The number of times values are differenced. If zero, the input
        is returned as-is.
    axis : int, optional
        The axis along which the difference is taken, default is the
        last axis.
    Returns
    -------
    diff : ndarray
        The n-th differences. The shape of the output is the same as `a`
        except along `axis` where the dimension is smaller by `n`. The
        type of the output is the same as the type of the difference
        between any two elements of `a`. This is the same as the type of
        `a` in most cases. A notable exception is `datetime64`, which
        results in a `timedelta64` output array.
    See Also
    --------
    gradient, ediff1d, cumsum
    Notes
    -----
    Type is preserved for boolean arrays, so the result will contain
    `False` when consecutive elements are the same and `True` when they
    differ.
    For unsigned integer arrays, the results will also be unsigned. This
    should not be surprising, as the result is consistent with
    calculating the difference directly:
    >>> u8_arr = np.array([1, 0], dtype=np.uint8)
    >>> np.diff(u8_arr)
    array([255], dtype=uint8)
    >>> u8_arr[1,...] - u8_arr[0,...]
    array(255, np.uint8)
    If this is not desirable, then the array should be cast to a larger
    integer type first:
    >>> i16_arr = u8_arr.astype(np.int16)
    >>> np.diff(i16_arr)
    array([-1], dtype=int16)
    Examples
    --------
    >>> x = np.array([1, 2, 4, 7, 0])
    >>> np.diff(x)
    array([ 1,  2,  3, -7])
    >>> np.diff(x, n=2)
    array([  1,   1, -10])
    >>> x = np.array([[1, 3, 6, 10], [0, 5, 6, 8]])
    >>> np.diff(x)
    array([[2, 3, 4],
           [5, 1, 2]])
    >>> np.diff(x, axis=0)
    array([[-1,  2,  0, -2]])
    >>> x = np.arange('1066-10-13', '1066-10-16', dtype=np.datetime64)
    >>> np.diff(x)
    array([1, 1], dtype='timedelta64[D]')
    """
    if n == 0:
        return a
    if n < 0:
        raise ValueError(
            "order must be non-negative but got " + repr(n))

    a = cp.asanyarray(a)
    nd = a.ndim
    # axis = normalize_axis_index(axis, nd)

    slice1 = [slice(None)] * nd
    slice2 = [slice(None)] * nd
    slice1[axis] = slice(1, None)
    slice2[axis] = slice(None, -1)
    slice1 = tuple(slice1)
    slice2 = tuple(slice2)

    op = not_equal if a.dtype == cp.bool_ else cp.subtract
    for _ in range(n):
        a = op(a[slice1], a[slice2])

    return a


# class interp1d(object):
# 
#     def __init__(self, xx, yy, bounds_error=False, fill_value=cp.nan):
#         self.input_len = len(xx)
#         if len(xx) != len(yy):
#             raise ValueError('Cannot interpolate uneven length arrays.')
#         xx = cp.concatenate((cp.asarray([-cp.inf]), xx, cp.asarray([cp.inf])))
#         yy = cp.concatenate((cp.asarray([cp.nan]), yy, cp.asarray([cp.nan])))
#         sorted_idxs = cp.argsort(xx)
#         self.x_sorted = xx[sorted_idxs]
#         self.y_sorted = yy[sorted_idxs]
#         self.differential_x = cp.concatenate((
#             self.x_sorted[1:] - self.x_sorted[:-1], cp.asarray([cp.nan])))
#         self.differential_y = cp.concatenate((
#             self.y_sorted[1:] - self.y_sorted[:-1], cp.asarray([cp.nan])))
#         self.bounds_error = bounds_error
#         self.fill_value = fill_value
# 
#     def __call__(self, x_values):
#         idxs_low = self._find_idx_below(x_values)
#         idxs_high = idxs_low + 1
#         bad_idxs = (idxs_low == 0) | (idxs_high == self.input_len + 1)
#         diffs = x_values - self.x_sorted[idxs_low]
#         output = (self.y_sorted[idxs_low] + self.differential_y[idxs_low] /
#                   self.differential_x[idxs_low] * diffs)
#         # import IPython; IPython.embed()
#         if cp.any(bad_idxs):
#             if self.bounds_error:
#                 raise ValueError('Values outside interpolation interval.')
#             else:
#                 output[bad_idxs] = self.fill_value
#         return output
#     
#     def _find_idx_below(self, values):
#         val_shape = values.shape
#         vals_flat = values.flatten()
#         idxs_low = cp.asarray([int(cp.sum(val > self.x_sorted)) - 1
#                                for val in vals_flat])
#         idxs_low = idxs_low.reshape(val_shape)
#         return idxs_low
