# cloud-conversion-tool

### Prerrequisitos:

docker

##### Ejecutar contenedores 


##### `docker-compose up`


#### acceder al contenedor Postgresql a traves de bash

##### `docker-compose run db bash`

#### login en postgres desde l bash del contenedor.
#### las credenciales del usuario postgres se encuentran en el archivo `docker-compose.yaml` 

##### `psql --host=db --username=test --dbname=test`