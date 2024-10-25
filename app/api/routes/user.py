from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import UUID
from sqlalchemy.orm import Session
from app.api.routes import dependencies
from app.services import user_service, order_service
from ... import models,schemas, database

router = APIRouter()

@router.post("/users/", response_model=schemas.UserCreateResponseModel, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreateRequestModel, db: Session = Depends(database.get_db)):
   return user_service.create_user(db=db,user=user)  


@router.get("/users/{user_id}", response_model=schemas.GetUserResponseModel, status_code=status.HTTP_200_OK)
async def get_user_details(
    user_id: UUID, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(dependencies.get_current_user)
):

    if not current_user.is_admin and current_user.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Access denied."
        )
        
    user = user_service.get_user_by_id(user_id, db)

    return schemas.GetUserResponseModel(user)

    

@router.put("/users/{user_id}", response_model=schemas.UserUpdateResponseModel, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: UUID,
    update_data: schemas.UserUpdateRequestModel,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):

    # Ensure users can only update their own details unless they are admin
    if user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You are not authorized to update this user."
        )

    updated_user = user_service.update_user_in_db(user_id, update_data, db)

    return schemas.UserUpdateResponseModel(updated_user)


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    # Ensure users can only delete their own account
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You are not authorized to delete this user."
        )

    user_service.delete_user_from_db(user_id, db)

    return {"message": f"User with ID {user_id} has been successfully deleted."}



@router.get("/users", response_model=list[schemas.GetUserResponseModel], status_code=status.HTTP_200_OK)
def get_users(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(dependencies.get_current_admin)  
):
    try:
        users = user_service.get_all_users(db)
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving users."
        )
    
@router.get("/users/{user_id}/orders", response_model=list[schemas.OrderDetailResponse], status_code=status.HTTP_200_OK)
def list_orders_for_user(
    user_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    if user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view these orders."
        )

    orders = order_service.get_orders_for_user(str(user_id), db)
    return orders


@router.put("/users/change_role", status_code=status.HTTP_200_OK)
def change_role(
    request: schemas.ChangeRoleRequest,
    current_user: models.User = Depends(dependencies.get_current_admin),
    db: Session = Depends(database.get_db)
):
    try:
        user_service.change_user_role(request.user_id, request.is_admin, db)
        return {"message": "User role updated successfully."}
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")