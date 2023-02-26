import os
import argparse
import csv
import torch
import piq
from tqdm import tqdm
from skimage.io import imread
from webui_utils.file_utils import get_files

@torch.no_grad()
def main():
    parser = argparse.ArgumentParser(description='Test PIQ')
    parser.add_argument("--path1", default="./images", type=str,
        help="Path to first set of files")
    parser.add_argument("--path2", default="./images", type=str,
        help="Path to second set of files")
    parser.add_argument("--file_type", default="png", type=str,
        help="File type of the files to resequence")
    args = parser.parse_args()
    files1 = get_files(args.path1, args.file_type)
    files2 = get_files(args.path2, args.file_type)
    file_count = len(files1)
    if file_count != len(files2):
        raise ValueError(f"error: both paths must have the same number of {args.file_type} files")

    report = {}

    FIELDS = ["index", "file1", "file2", "brisque_index1", "brisque_index2", "dss_index",
              "fsim_index", "gmsd_index", "haarpsi_index", "mdsi_index", "ms_gmsd_index",
              "psnr_index", "ssim_index", "tv_index1", "tv_index2", "vif_index", "vsi_index",
              "srsim_index"]

    for index in tqdm(range(file_count), desc="Frames"):
        file1 = files1[index]
        file2 = files2[index]
        _, name1 = os.path.split(file1)
        _, name2 = os.path.split(file2)

        data = test(index, file1, file2)
        data["index"] = index
        data["file1"] = name1
        data["file2"] = name2
        report[index] = data

    row_array = [report[index] for index, _ in enumerate(files1)]
    with open("./test_piq2.csv", 'w', encoding="UTF-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = FIELDS)
        writer.writeheader()
        writer.writerows(row_array)


def test(index, img1_file, img2_file):
    # Read RGB image and it's noisy version
    x = torch.tensor(imread(img1_file)).permute(2, 0, 1)[None, ...] / 255.0
    y = torch.tensor(imread(img2_file)).permute(2, 0, 1)[None, ...] / 255.0

    if torch.cuda.is_available():
        # Move to GPU to make computaions faster
        x = x.cuda()
        y = y.cuda()

    # To compute BRISQUE score as a measure, use lower case function from the library
    try:
        brisque_index1: torch.Tensor = piq.brisque(x, data_range=1., reduction='none')
        brisque_index1 = brisque_index1.item()
    except:
        brisque_index1 = 0.0
    try:
        brisque_index2: torch.Tensor = piq.brisque(y, data_range=1., reduction='none')
        brisque_index2 = brisque_index2.item()
    except:
        brisque_index2 = 0.0

    # In order to use BRISQUE as a loss function, use corresponding PyTorch module.
    # Note: the back propagation is not available using torch==1.5.0.
    # Update the environment with latest torch and torchvision.
    # brisque_loss: torch.Tensor = piq.BRISQUELoss(data_range=1., reduction='none')(x)
    # print(f"BRISQUE index: {brisque_index.item():0.4f}, loss: {brisque_loss.item():0.4f}")

    # To compute Content score as a loss function, use corresponding PyTorch module
    # By default VGG16 model is used, but any feature extractor model is supported.
    # Don't forget to adjust layers names accordingly. Features from different layers can be weighted differently.
    # Use weights parameter. See other options in class docstring.
    # content_loss = piq.ContentLoss(
    #     feature_extractor="vgg16", layers=("relu3_3",), reduction='none')(x, y)
    # print(f"ContentLoss: {content_loss.item():0.4f}")

    # To compute DISTS as a loss function, use corresponding PyTorch module
    # By default input images are normalized with ImageNet statistics before forwarding through VGG16 model.
    # If there is no need to normalize the data, use mean=[0.0, 0.0, 0.0] and std=[1.0, 1.0, 1.0].
    # dists_loss = piq.DISTS(reduction='none')(x, y)
    # print(f"DISTS: {dists_loss.item():0.4f}")

    # To compute DSS as a measure, use lower case function from the library
    dss_index: torch.Tensor = piq.dss(x, y, data_range=1., reduction='none')
    # In order to use DSS as a loss function, use corresponding PyTorch module
    # dss_loss = piq.DSSLoss(data_range=1., reduction='none')(x, y)
    # print(f"DSS index: {dss_index.item():0.4f}, loss: {dss_loss.item():0.4f}")

    # To compute FSIM as a measure, use lower case function from the library
    fsim_index: torch.Tensor = piq.fsim(x, y, data_range=1., reduction='none')
    # In order to use FSIM as a loss function, use corresponding PyTorch module
    # fsim_loss = piq.FSIMLoss(data_range=1., reduction='none')(x, y)
    # print(f"FSIM index: {fsim_index.item():0.4f}, loss: {fsim_loss.item():0.4f}")

    # To compute GMSD as a measure, use lower case function from the library
    # This is port of MATLAB version from the authors of original paper.
    # In any case it should me minimized. Usually values of GMSD lie in [0, 0.35] interval.
    gmsd_index: torch.Tensor = piq.gmsd(x, y, data_range=1., reduction='none')
    # In order to use GMSD as a loss function, use corresponding PyTorch module:
    # gmsd_loss: torch.Tensor = piq.GMSDLoss(data_range=1., reduction='none')(x, y)
    # print(f"GMSD index: {gmsd_index.item():0.4f}, loss: {gmsd_loss.item():0.4f}")

    # To compute HaarPSI as a measure, use lower case function from the library
    # This is port of MATLAB version from the authors of original paper.
    haarpsi_index: torch.Tensor = piq.haarpsi(x, y, data_range=1., reduction='none')
    # In order to use HaarPSI as a loss function, use corresponding PyTorch module
    # haarpsi_loss: torch.Tensor = piq.HaarPSILoss(data_range=1., reduction='none')(x, y)
    # print(f"HaarPSI index: {haarpsi_index.item():0.4f}, loss: {haarpsi_loss.item():0.4f}")

    # To compute LPIPS as a loss function, use corresponding PyTorch module
    # lpips_loss: torch.Tensor = piq.LPIPS(reduction='none')(x, y)
    # print(f"LPIPS: {lpips_loss.item():0.4f}")

    # To compute MDSI as a measure, use lower case function from the library
    mdsi_index: torch.Tensor = piq.mdsi(x, y, data_range=1., reduction='none')
    # In order to use MDSI as a loss function, use corresponding PyTorch module
    # mdsi_loss: torch.Tensor = piq.MDSILoss(data_range=1., reduction='none')(x, y)
    # print(f"MDSI index: {mdsi_index.item():0.4f}, loss: {mdsi_loss.item():0.4f}")

    # # To compute MS-SSIM index as a measure, use lower case function from the library:
    # ms_ssim_index: torch.Tensor = piq.multi_scale_ssim(x, y, data_range=1.)
    # # In order to use MS-SSIM as a loss function, use corresponding PyTorch module:
    # ms_ssim_loss = piq.MultiScaleSSIMLoss(data_range=1., reduction='none')(x, y)
    # print(f"MS-SSIM index: {ms_ssim_index.item():0.4f}, loss: {ms_ssim_loss.item():0.4f}")

    # To compute Multi-Scale GMSD as a measure, use lower case function from the library
    # It can be used both as a measure and as a loss function. In any case it should me minimized.
    # By default scale weights are initialized with values from the paper.
    # You can change them by passing a list of 4 variables to scale_weights argument during initialization
    # Note that input tensors should contain images with height and width equal 2 ** number_of_scales + 1 at least.
    ms_gmsd_index: torch.Tensor = piq.multi_scale_gmsd(
        x, y, data_range=1., chromatic=True, reduction='none')
    # In order to use Multi-Scale GMSD as a loss function, use corresponding PyTorch module
    # ms_gmsd_loss: torch.Tensor = piq.MultiScaleGMSDLoss(
    #     chromatic=True, data_range=1., reduction='none')(x, y)
    # print(f"MS-GMSDc index: {ms_gmsd_index.item():0.4f}, loss: {ms_gmsd_loss.item():0.4f}")

    # To compute PSNR as a measure, use lower case function from the library.
    psnr_index = piq.psnr(x, y, data_range=1., reduction='none')
    # print(f"PSNR index: {psnr_index.item():0.4f}")

    # To compute PieAPP as a loss function, use corresponding PyTorch module:
    # pieapp_loss: torch.Tensor = piq.PieAPP(reduction='none', stride=32)(x, y)
    # print(f"PieAPP loss: {pieapp_loss.item():0.4f}")

    # To compute SSIM index as a measure, use lower case function from the library:
    ssim_index = piq.ssim(x, y, data_range=1.)
    # In order to use SSIM as a loss function, use corresponding PyTorch module:
    # ssim_loss: torch.Tensor = piq.SSIMLoss(data_range=1.)(x, y)
    # print(f"SSIM index: {ssim_index.item():0.4f}, loss: {ssim_loss.item():0.4f}")

    # To compute Style score as a loss function, use corresponding PyTorch module:
    # By default VGG16 model is used, but any feature extractor model is supported.
    # Don't forget to adjust layers names accordingly. Features from different layers can be weighted differently.
    # Use weights parameter. See other options in class docstring.
    # style_loss = piq.StyleLoss(feature_extractor="vgg16", layers=("relu3_3",))(x, y)
    # print(f"Style: {style_loss.item():0.4f}")

    # To compute TV as a measure, use lower case function from the library:
    tv_index1: torch.Tensor = piq.total_variation(x)
    tv_index2: torch.Tensor = piq.total_variation(y)
    # In order to use TV as a loss function, use corresponding PyTorch module:
    # tv_loss: torch.Tensor = piq.TVLoss(reduction='none')(x)
    # print(f"TV index: {tv_index.item():0.4f}, loss: {tv_loss.item():0.4f}")

    # To compute VIF as a measure, use lower case function from the library:
    vif_index: torch.Tensor = piq.vif_p(x, y, data_range=1.)
    # In order to use VIF as a loss function, use corresponding PyTorch class:
    # vif_loss: torch.Tensor = piq.VIFLoss(sigma_n_sq=2.0, data_range=1.)(x, y)
    # print(f"VIFp index: {vif_index.item():0.4f}, loss: {vif_loss.item():0.4f}")

    # To compute VSI score as a measure, use lower case function from the library:
    vsi_index: torch.Tensor = piq.vsi(x, y, data_range=1.)
    # In order to use VSI as a loss function, use corresponding PyTorch module:
    # vsi_loss: torch.Tensor = piq.VSILoss(data_range=1.)(x, y)
    # print(f"VSI index: {vsi_index.item():0.4f}, loss: {vsi_loss.item():0.4f}")

    # To compute SR-SIM score as a measure, use lower case function from the library:
    srsim_index: torch.Tensor = piq.srsim(x, y, data_range=1.)
    # In order to use SR-SIM as a loss function, use corresponding PyTorch module:
    # srsim_loss: torch.Tensor = piq.SRSIMLoss(data_range=1.)(x, y)
    # print(f"SR-SIM index: {srsim_index.item():0.4f}, loss: {srsim_loss.item():0.4f}")

    return {
        "brisque_index1" : brisque_index1,
        "brisque_index2" : brisque_index2,
        "dss_index" : dss_index.item(),
        "fsim_index" : fsim_index.item(),
        "gmsd_index" : gmsd_index.item(),
        "haarpsi_index" : haarpsi_index.item(),
        "mdsi_index" : mdsi_index.item(),
        "ms_gmsd_index" : ms_gmsd_index.item(),
        "psnr_index" : psnr_index.item(),
        "ssim_index" : ssim_index.item(),
        "tv_index1" : tv_index1.item(),
        "tv_index2" : tv_index2.item(),
        "vif_index" : vif_index.item(),
        "vsi_index" : vsi_index.item(),
        "srsim_index" : srsim_index.item()
    }

if __name__ == '__main__':
    main()