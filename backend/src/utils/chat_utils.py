from database.db import chats_collection


async def get_chat_summaries(filter_query: dict):
    """
    Returns a lightweight list of chats matching the filter.
    ObjectIds are converted to strings directly in the database query,
    so no manual iteration is needed after fetching.
    """
    cursor = await chats_collection.aggregate([
        {"$match": filter_query},
        {
            "$project": {
                "id": {"$toString": "$_id"},
                "status": 1,
                "created_at": 1,
                "updated_at": 1,
                "_id": 0,
            }
        }
    ])

    return await cursor.to_list(None)


async def get_chats_with_messages(filter_query: dict):
    pipeline = [
        {"$match": filter_query},
        # Join with messages collection to get all messages for each chat
        {
            "$lookup": {
                "from": "messages",
                "localField": "_id",
                "foreignField": "chat_id",
                "as": "messages",
            }
        },
        # Convert chat ObjectIds to strings
        {
            "$addFields": {
                "id": {"$toString": "$_id"},
                "assigned_professional_id": {
                    "$cond": [
                        {"$ifNull": ["$assigned_professional_id", False]},
                        {"$toString": "$assigned_professional_id"},
                        None
                    ]
                },
                "user_id": {"$toString": "$user_id"}
            }
        },
        # Convert each message _id to string
        {
            "$set": {
                "messages": {
                    "$map": {
                        "input": "$messages",
                        "as": "msg",
                        "in": {
                            "$mergeObjects": [
                                "$$msg",
                                {"id": {"$toString": "$$msg._id"}, "_id": "$$REMOVE"}
                            ]
                        }
                    }
                }
            }
        },
        {"$sort": {"updated_at": -1}}
    ]

    cursor = await chats_collection.aggregate(pipeline)

    return await cursor.to_list(None)
