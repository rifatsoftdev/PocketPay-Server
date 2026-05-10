import cloudinary
import cloudinary.uploader


class CloudinaryStorage:
    def __init__(self, cloud_name, api_key, api_secret):
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )

    def upload_file(self, file_path, public_id, file_type="image"):
        """
        file_type: image | video | raw
        """
        result = cloudinary.uploader.upload(
            file_path,
            resource_type=file_type,
            public_id=public_id,
            overwrite=True
        )

        return {
            "public_id": result["public_id"],
            "url": result["secure_url"]
        }

    def delete_file(self, public_id, file_type="image"):
        """
        public_id: id obtained during upload
        """
        result = cloudinary.uploader.destroy(
            public_id,
            resource_type=file_type
        )

        return result

