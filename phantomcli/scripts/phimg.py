#!/usr/bin/env python3

# standard library imports
import logging
import time

from collections import defaultdict

# third party imports
import click
import matplotlib.pyplot as plt

# package imports
from phantomcli.network import PhantomSocket
from phantomcli.scripts.util import logging_config, logging_format, formats
from phantomcli.scripts.util import log_help, format_help


@click.command('phget')
@click.option('--network', '-n', default='e', help='')
@click.option('--format', '-f', default='P16', help=format_help)
@click.option('--dataport', '-p', default=60000)
@click.option('--dataip', '-i', default='127.0.0.1')
@click.option('--log', '-l', default='ERROR', help=log_help)
@click.argument('ip')
def command(ip, log, dataip, dataport, format, network):
    """
    Given the IP ADDRESS of the camera, this will open a secondary channel to the camera to receive the raw data of
    the current frame. Once the data has been transmitted completely a new window will open, displaying the image from
    the camera.
    """
    logging.basicConfig(
        format=logging_format,
        level=logging_config[log]
    )

    # Creating the phantom socket to communicate with the camera
    phantom_socket = PhantomSocket(
        ip,
        img_format=formats[format],
        data_ip=dataip,
        data_port=dataport,
        network_type=network
    )
    phantom_socket.connect()
    click.echo('CONNECTED TO THE PHANTOM CAMERA')

    if network == 'x':
        phantom_socket.start_data_server()
    else:
        phantom_socket.start_data_server()
        phantom_socket.startdata()
    click.echo('STARTED THE DATA SERVER')

    phantom_image = phantom_socket.img()
    click.echo('RECEIVED IMAGE FROM PHANTOM')

    plt.imshow(phantom_image.array, cmap='gray')
    plt.show()

    phantom_socket.disconnect()


if __name__ == '__main__':
    command()
