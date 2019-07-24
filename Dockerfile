# HydroShare HIS 1.0.0
# Django 2.1.5


FROM ubuntu:18.04


MAINTAINER Kenneth Lippold kjlippold@gmail.com


# Apt Setup ----------------------------------------------------------------------------------------------#

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install wget emacs vim sudo bzip2 nginx supervisor -y


# Create hisapp user --------------------------------------------------------------------------------------#

RUN adduser --disabled-password --gecos '' hisapp
RUN adduser hisapp sudo
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER hisapp

ENV HIS_HOME /home/hisapp
WORKDIR $HIS_HOME
RUN chmod a+rwx $HIS_HOME


# Place Application Files --------------------------------------------------------------------------------#

RUN mkdir hydroshare_his

COPY environment.yml $HIS_HOME
COPY hydroshare_his/ $HIS_HOME/hydroshare_his
COPY startup.sh $HIS_HOME
COPY hydroshare_his.conf /etc/nginx/conf.d/

RUN sudo chown -R hisapp $HIS_HOME/hydroshare_his


# Setup Conda Environment --------------------------------------------------------------------------------#

RUN wget https://repo.continuum.io/miniconda/Miniconda2-4.5.12-Linux-x86_64.sh
RUN bash Miniconda2-4.5.12-Linux-x86_64.sh -b
RUN rm Miniconda2-4.5.12-Linux-x86_64.sh

ENV PATH /home/hisapp/miniconda2/bin:$PATH

RUN conda update conda
RUN conda update --all


RUN conda env create -f environment.yml
RUN echo "source activate his" > ~/.bashrc


# Expose Ports -------------------------------------------------------------------------------------------#

EXPOSE 8060


# Run HydroShare HIS ----------------------------------------------------------------------------------------#

RUN sudo chmod +x startup.sh
USER root
CMD ["./startup.sh"]
