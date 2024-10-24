import torch
import torch.nn as nn

class ConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(ConvBlock, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        x = self.conv(x)
        return x

class EncoderBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(EncoderBlock, self).__init__()
        self.conv_block = ConvBlock(in_channels, out_channels)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

    def forward(self, x):
        conv = self.conv_block(x)
        x_pooled = self.pool(conv)
        return conv, x_pooled

class DecoderBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(DecoderBlock, self).__init__()
        self.upconv = nn.ConvTranspose2d(in_channels, in_channels//2, kernel_size=2, stride=2)
        self.conv_block = ConvBlock(in_channels, out_channels)

    def forward(self, x, skip):
        x = self.upconv(x)
        x = torch.cat([x, skip], dim=1)
        x = self.conv_block(x)
        return x


# Classic Unet
# -------------------------------------
class Unet(nn.Module):
    def __init__(self, input_channels, num_classes, num_filters, dropout = 0.1):
        super(Unet, self).__init__()
        self.encoders = nn.ModuleList()
        self.decoders = nn.ModuleList()
        self.dropout = nn.Dropout(dropout)

        # Encoder
        for i, filters in enumerate(num_filters[:-1]):
            self.encoders.append(EncoderBlock(input_channels if i == 0 else num_filters[i-1], filters))

        # Bottleneck
        self.bottleneck = ConvBlock(num_filters[-2], num_filters[-1])

        # Decoder
        num_filters_reversed = num_filters[::-1]
        for i in range(len(num_filters) - 1):
            in_channels = num_filters_reversed[i]
            out_channels = num_filters_reversed[i + 1]  # This is the output channel size after ConvBlock
            self.decoders.append(DecoderBlock(in_channels, out_channels))

        # Classifier
        self.final_conv = nn.Conv2d(num_filters[0], num_classes, kernel_size=1)

    def forward(self, x):
        skips = []
        for encoder in self.encoders:
            x, x_pooled = encoder(x)
            skips.append(x)
            x = x_pooled

        x = self.bottleneck(x)
        x = self.dropout(x)

        # reverse the skips list
        skips_reverse = skips[::-1]

        for i, decoder in enumerate(self.decoders):
            x = decoder(x, skips_reverse[i])

        x = self.final_conv(x)

        return x


# Unet with Two Decoders
# -------------------------------------
class TwoLeggedUnet(nn.Module):
    def __init__(self, input_channels, num_classes, num_filters, dropout=0.1):
        super(TwoLeggedUnet, self).__init__()
        self.encoders = nn.ModuleDict()
        self.decoders1 = nn.ModuleDict()
        self.decoders2 = nn.ModuleDict()
        self.dropout = nn.Dropout(dropout)

        # Encoder
        for i, filters in enumerate(num_filters[:-1]):
            self.encoders[f'encoder_{i}'] = EncoderBlock(input_channels if i == 0 else num_filters[i-1], filters)

        # Bottleneck
        self.bottleneck = ConvBlock(num_filters[-2], num_filters[-1])

        # Decoder 1
        num_filters_reversed = num_filters[::-1]
        for i in range(len(num_filters) - 1):
            in_channels = num_filters_reversed[i]
            out_channels = num_filters_reversed[i + 1]
            self.decoders1[f'decoder1_{i}'] = DecoderBlock(in_channels, out_channels)

        # Decoder 2
        for i in range(len(num_filters) - 1):
            in_channels = num_filters_reversed[i]
            out_channels = num_filters_reversed[i + 1]
            self.decoders2[f'decoder2_{i}'] = DecoderBlock(in_channels, out_channels)

        # Classifiers
        self.final_conv1 = nn.Conv2d(num_filters[0], num_classes // 2, kernel_size=1)
        self.final_conv2 = nn.Conv2d(num_filters[0], num_classes // 2, kernel_size=1)

    def forward(self, x):
        skips = []
        for i, encoder in enumerate(self.encoders.values()):
            x, x_pooled = encoder(x)
            skips.append(x)
            x = x_pooled

        x = self.bottleneck(x)
        x = self.dropout(x)

        # reverse the skips list
        skips_reverse = skips[::-1]

        # Decoder 1
        x1 = x
        for i, decoder in enumerate(self.decoders1.values()):
            x1 = decoder(x1, skips_reverse[i])
        x1 = self.final_conv1(x1)

        # Decoder 2
        x2 = x
        for i, decoder in enumerate(self.decoders2.values()):
            x2 = decoder(x2, skips_reverse[i])
        x2 = self.final_conv2(x2)

        x_concat = torch.cat([x1, x2], dim=1)
        
        return x_concat
    
# Original Unet (Old Code)
'''
class ConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(ConvBlock, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        x = self.conv(x)
        return x

class EncoderBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(EncoderBlock, self).__init__()
        self.conv_block = ConvBlock(in_channels, out_channels)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

    def forward(self, x):
        conv = self.conv_block(x)
        x_pooled = self.pool(conv)
        return conv, x_pooled

class DecoderBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(DecoderBlock, self).__init__()
        self.upconv = nn.ConvTranspose2d(in_channels, in_channels//2, kernel_size=2, stride=2)
        self.conv_block = ConvBlock(in_channels, out_channels)

    def forward(self, x, skip):
        x = self.upconv(x)
        x = torch.cat([x, skip], dim=1)
        x = self.conv_block(x)
        return x
'''
class OriginalUnet(nn.Module):
    def __init__(self, input_channels, num_classes, num_filters):
        super(OriginalUnet, self).__init__()
        self.encoders = nn.ModuleList()
        self.decoders = nn.ModuleList()

        # Encoder
        for i, filters in enumerate(num_filters[:-1]):
            self.encoders.append(EncoderBlock(input_channels if i == 0 else num_filters[i-1], filters))

        # Bottleneck
        self.bottleneck = ConvBlock(num_filters[-2], num_filters[-1])

        # Decoder
        num_filters_reversed = num_filters[::-1]
        for i in range(len(num_filters) - 1):
            in_channels = num_filters_reversed[i]
            out_channels = num_filters_reversed[i + 1]  # This is the output channel size after ConvBlock
            self.decoders.append(DecoderBlock(in_channels, out_channels))

        # Classifier
        self.final_conv = nn.Conv2d(num_filters[0], num_classes, kernel_size=1)

    def forward(self, x):
        skips = []
        for encoder in self.encoders:
            x, x_pooled = encoder(x)
            skips.append(x)
            x = x_pooled

        x = self.bottleneck(x)

        # reverse the skips list
        skips_reverse = skips[::-1]

        for i, decoder in enumerate(self.decoders):
            x = decoder(x, skips_reverse[i])

        x = self.final_conv(x)

        return x

