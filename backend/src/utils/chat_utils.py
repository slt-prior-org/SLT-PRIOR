from database.db import chats_collection


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

    return await chats_collection.aggregate(pipeline).to_list(None)
