import numpy as np
import xarray as xr


def scale(image):
    ''' image will be rescaled to a range of 0 – 1'''

    mean = np.mean(image)
    std = np.std(image)

    new_min = mean - 2*std
    new_max = mean + 2*std

    # subtract new_min
    image = image - new_min
    # divide by min-max range
    image = image / (new_max - new_min)
    
    # clip values outside of range [0,1]
    image = np.clip(image, a_min=0, a_max=1)

    return(image)

def nbr(xarray_image):
    '''
    calculates nbr (normalised burn ratio) from a given xarray image'''

    NIR = xarray_image.sel(band=["B08"]).squeeze()
    SWIR = xarray_image.sel(band=["B12"]).squeeze()
    return (NIR -SWIR) / (NIR + SWIR)

def ndwi(xarray_image):
    '''calculates ndwi index from a given xarray image'''
    GREEN = xarray_image.sel(band=["B03"]).squeeze()
    NIR = xarray_image.sel(band=["B08"]).squeeze()
    return (GREEN - NIR) / (NIR + GREEN)

def water_mask(ndwi_image, th):
    '''
    creates water mask:
    0= no water
    1= water
    input ndwi image (xarray) and treshold
    returns water mask and legend'''
    # new xarray
    ndwi_classes = xr.full_like(ndwi_image, fill_value=np.nan, dtype=int)

    #reclassify
    ndwi_classes = xr.where(ndwi_image <= th , 0, ndwi_classes)
    ndwi_classes = xr.where(ndwi_image > th, 1, ndwi_classes)

    # legend
    legend = {
        0: "no water",
        1: "water"
    }

    return ndwi_classes, legend

def apply_water_mask(nbr_data, water_mask):
    '''
    mask nbr data where the water mask = 1 (water)'''
    return xr.where(water_mask == 1, np.nan, nbr_data)

def reclassify_dnbr(dnbr):

    '''
    reclassifies an dnbr image to burn severity classes
    See also:
    https://un-spider.org/advisory-support/recommended-practices/recommended-practice-burn-severity/in-detail/normalized-burn-ratio
    '''

    # new xarray
    dnbr_classes = xr.full_like(dnbr, fill_value=np.nan, dtype=int)

    #reclassify
    dnbr_classes = xr.where(np.isnan(dnbr), 0, dnbr_classes)    
    dnbr_classes = xr.where(dnbr <= -0.251, 1, dnbr_classes)
    dnbr_classes = xr.where((dnbr > -0.251) & (dnbr <= -0.101), 2, dnbr_classes)
    dnbr_classes = xr.where((dnbr > -0.101) & (dnbr <= 0.099), 3, dnbr_classes)
    dnbr_classes = xr.where((dnbr > 0.099) & (dnbr <= 0.269), 4, dnbr_classes)
    dnbr_classes = xr.where((dnbr > 0.269) & (dnbr <= 0.439), 5, dnbr_classes)
    dnbr_classes = xr.where((dnbr > 0.439) & (dnbr <= 0.659), 6, dnbr_classes)
    dnbr_classes = xr.where(dnbr > 0.659, 7, dnbr_classes)

    # legend 
    legend = {
        0: "Water",
        1: "Enhanced regrowth, high",
        2: "Enhanced regrowth, low",
        3: "Unburned",
        4: "Low severity",
        5: "Moderate - low severity",
        6: "Moderate - high severity",
        7: "High severity"
    }

    return dnbr_classes, legend

def ndvi(xarray_image):
    '''calculates ndvi index from a given xarray'''
    RED = xarray_image.sel(band=["B04"]).squeeze()
    NIR = xarray_image.sel(band=["B08"]).squeeze()
    return (NIR -RED) / (NIR + RED)


def burn_mask(dnbr_image, th):
    '''
    returns burn mask (burned, not burned) for dnbr image
    input: dnbr image(xarray), th = treshold (should be 0.1)
    https://un-spider.org/advisory-support/recommended-practices/recommended-practice-burn-severity/in-detail/normalized-burn-ratio)
    '''
    #new xarray
    dnbr_binary = xr.full_like(dnbr_image, fill_value=np.nan, dtype=int)

    #reclassify
    dnbr_binary = xr.where(dnbr_image <= th , 0, dnbr_binary)
    dnbr_binary = xr.where(dnbr_image > th, 1, dnbr_binary)

    # legend
    legend = {
        0: "not burned",
        1: "burned"
    }

    return dnbr_binary, legend

def apply_burn_mask(dnbr_image, burn_mask):
    '''
    Masks data where the the burn mask is 0 (not burned)
    Input: dnbr image (xarray), burn_mask
    '''
    return xr.where(burn_mask == 0, np.nan, dnbr_image)

def cloud_mask(scl_layer):
    # new xarray
    scl_binary = xr.full_like(scl_layer, fill_value=np.nan, dtype=int)

    # reclassify
    scl_binary = xr.where(((scl_layer > 3) & (scl_layer < 8)) | (scl_layer > 9), 1, scl_binary)
    scl_binary = xr.where((scl_layer < 4) | ((scl_layer > 7) & (scl_layer < 10)), 0, scl_binary)

    legend_scl = {
        0: "cloud",
        1: "no cloud"
    }

    return scl_binary, legend_scl

def apply_cloud_mask(image, cloud_mask):

    return xr.where(cloud_mask == 0, np.nan, image) # if mask = 0 (cloud) -> nan; else return image value.